# coding=utf-8
import logging
import math
import typing
from django.http import request
import stripe
import json

from builtins import str as text
from datetime import timedelta, date
from decimal import Decimal
from uuid import uuid4

import sentry_sdk

from srbc.models import Profile, Subscription, StripeSubscription, Tariff
from srbc.utils.stripe import get_vat_tax_rates

from content.models import TGNotificationTemplate
from content.utils import store_dialogue_reply
from crm.models import Campaign, Payment, TariffHistory,  StripePayment
from crm.utils.subscription import is_upgrade
from crm.utils.yandex_subscription import cancel_yandex_subscription

#Yandex checkout doesn't work anymore
#from yandex_checkout import Configuration, Payment as YandexPayment

#yookassa is the new payment module
from yookassa import Configuration, Payment as YandexPayment

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django_telegrambot.apps import DjangoTelegramBot
from django.core.exceptions import ObjectDoesNotExist
from django.db import ProgrammingError, transaction
from django.db.models.signals import pre_save
from django.urls import reverse
from django.utils.timezone import localtime


from paypal.standard.models import ST_PP_COMPLETED, ST_PP_PENDING
from paypal.standard.ipn.signals import valid_ipn_received
from paypal.standard.forms import PayPalPaymentsForm

from dateutil.parser import parse

from sentry_sdk import capture_exception

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)

Configuration.configure(settings.YANDEX_MONEY_SHOP_ID, settings.YANDEX_MONEY_SHOP_PASSWORD)
logger = logging.getLogger(__name__)


@transaction.atomic
def cancel_payment(order):
    if not order.payment_id:
        return order

    if order.status == 'CANCELED':
        return order

    logger.info(
        'Cancelling payment #%s (%s)' % (
            order.id,
            order.payment_id,
        )
    )

    # Locking
    Profile.objects.select_for_update().get(user=order.user)

    # payment_object = Payment.cancel(payment_id=str(order.payment_id))
    order.status = 'CANCELED'
    order.save(update_fields=['status'])

    return order


@transaction.atomic
def check_payment(order):
    if not order.payment_id:
        return order

    if order.status == 'CANCELED':
        return order

    if order.status == 'APPROVED':
        return order

    # Locking
    Profile.objects.select_for_update().get(user=order.user)

    if order.payment_provider in ['YA', 'YM']:
        payment_object = YandexPayment.find_one(str(order.payment_id))
        logger.info("Yandex Payment Order received: %s" % vars(payment_object))
        if payment_object.status == 'canceled':
            if order.discount_code:
                order.discount_code.is_applied = False
                order.discount_code.save()
            order.status = Payment.STATUS_CANCELED
            order.save()

        if payment_object.paid and '%0.2f' % payment_object.amount.value == '%0.2f' % order.amount \
                and order.currency == payment_object.amount.currency:
            order.status = Payment.STATUS_APPROVED
            order.paid_at = parse(payment_object.captured_at)
            order.save()
            return order

        if '%0.2f' % payment_object.amount.value != '%0.2f' % order.amount \
                or order.currency != payment_object.amount.currency:
            raise ArithmeticError('%0.2f != %0.2f' % (payment_object.amount.value, order.amount))

    return order


def confirm_yandex_payment(payment_object):
    # получили нотификацию о конфирме

    # вывалится напрямую в сентру, кажется что так ок
    payment = Payment.objects.get(payment_id=payment_object.id)

    if '%0.2f' % payment_object.amount.value != '%0.2f' % payment.amount \
            or payment.currency != payment_object.amount.currency:
        raise ArithmeticError('%0.2f != %0.2f' % (payment_object.amount.value, payment.amount))

    else:
        confirm_order(payment)


def cancel_yandex_payment(payment_object):
    # получили нотификацию об отмене

    # вывалится напрямую в сентру, кажется что так ок
    payment = Payment.objects.get(payment_id=payment_object.id)

    # лок специально оставлен и закомменчен
    # Locking
    # Profile.objects.select_for_update().get(user=order.user)

    if payment.discount_code:
        payment.discount_code.is_applied = False
        payment.discount_code.save()
    payment.status = Payment.STATUS_CANCELED
    payment.save()


def get_payment_type(user):
    if user.profile.is_in_club:
        return 'CLUB'

    if user.profile.tariff_next:
        return user.profile.tariff_next.tariff_group.communication_mode
    # FIXME точно надо? или обойдемся?
    elif user.profile.tariff:
        return user.profile.tariff.tariff_group.communication_mode
    elif user.application.tariff:
        return user.application.tariff.tariff_group.communication_mode
    else:
        return None


def get_payment_amount(order):
    """

    :param order:
    :type order: crm.models.Payment
    """
    currency_by_provider = settings.CURRENCY_BY_PROVIDER

    price_list = {
        'CLUB': {
            'RUB': 4000.00,
            'EUR': 50.00,
        },
        'CHAT': {
            'RUB': 48000.00,
            'EUR': 660.00,
        },
        'CHANNEL': {
            'RUB': 10000.00,
            'EUR': 140.00,
        },
    }
    currency = currency_by_provider.get(str(order.payment_provider), 'RUB')

    if order.tariff:
        if currency == 'RUB':
            amount = order.tariff.fee_rub
        elif currency == 'EUR':
            amount = order.tariff.fee_eur
        else:
            raise NotImplemented('Unknown currency: %s (paid via %s)' % (currency, order.payment_provider,))

    else:
        order_item = price_list.get(str(order.payment_type))

        amount = Decimal(order_item.get(currency))

        if order.discount_code:
            amount *= Decimal(1.0) - order.discount_code.dicount_percent / Decimal(100.0)

        amount = math.floor(amount * 100) / 100.0

    return amount, currency


# TODO, если все же будем вводить гугл/андрйд подписки надо будет сделать общий класс/методы


def update_stripe_subscription_id(data):
    # Добавляем в подписку страйповский subscription_id
    try:
        stripe_subscription = StripeSubscription.objects.get(subscription_id=data.metadata.get('subscription_id'))
        stripe_subscription.stripe_subscription_id = data.subscription
        stripe_subscription.save(update_fields=['stripe_subscription_id'])
    except ObjectDoesNotExist:
        # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
        logger.error('Update subscription. Subscription_id not found %s', data.metadata.get('subscription_id'))
    except Exception as e:
        logger.error('Update subscription. Subscription_id %s. Error = %s', data.metadata.get('subscription_id'), e)


def confirm_stripe_subscription_payment(data, is_first_payment):
    # оплата за подписку (не важно продление или нет)
    try:
        stripe_subscription = StripeSubscription.objects.get(stripe_subscription_id=data.subscription)

        # проверяем не обработан ли у нас уже этот платеж,
        # ситуация может возникнуть, когда мы обработали эвэнт от страйпа, но он не получил от нас ответ
        # и повторно присылает этот эвэнт. Просто возвращаем, что все ок
        is_already_confirmed = Payment.objects.filter(
            stripe_payment__invoice_id=data.id,
            status=Payment.STATUS_APPROVED
        ).exists()

        if is_already_confirmed:
            return

        # по идее в одной транзакции должны обновить статус подписки и создать тарифф хистори
        with transaction.atomic():

            # в случае, когда имея волновой тариф оплатили подписку наперед - придет обычный счет
            # нам надо выделить его из массы и НЕ СОЗДАВАТЬ для него ТХ, пейменты и ТД,
            # просто перевести подписку в статус активности
            if data.lines['data'][0].description and data.amount_paid == 0:
                # если пользователь оформляет подписку, то гасим ему возможность оплаты волнового тарифв
                # stripe_subscription.subscription.user.application.is_payment_allowed = False
                # stripe_subscription.subscription.user.application.save(update_fields=['is_payment_allowed'])

                # меняем именно через tariff_next - в триггере скинется и is_payment_allowed
                # это сразу обрежет возможность восстановления, но это ок - потом руками восстановят
                stripe_subscription.subscription.user.profile.tariff_next = None
                stripe_subscription.subscription.user.profile.save(update_fields=['tariff_next'])
            else:
                # Locking
                Profile.objects.select_for_update().get(user=stripe_subscription.subscription.user)

                stripe_payment = StripePayment()
                stripe_payment.invoice_id = data.id
                stripe_payment.save()

                payment = Payment()
                payment.user = stripe_subscription.subscription.user
                # подписка всегда в рамках одного тарифа
                payment.tariff = stripe_subscription.subscription.tariff
                payment.payment_provider = 'Stripe'
                # TODO возможно вынести в функцию, пока только тут такой тип -пропишем
                payment.payment_type = Payment.PAYMENT_TYPE_NON_WAVE
                payment.status = Payment.STATUS_APPROVED
                payment.amount = Decimal(data.amount_paid) / 100  # присылает в евро центах
                payment.currency = data.currency.upper()
                payment.subscription = stripe_subscription.subscription
                payment.stripe_payment = stripe_payment
                payment.save()

                tariff_history = TariffHistory()
                tariff_history.payment = payment
                tariff_history.tariff = payment.tariff
                tariff_history.user = payment.user
                tariff_history.is_active = True
                tariff_history.wave = None  # TODO пока так, возможно потом придется менять
                # дату фром берем или из прошлой записи или равной now

                last_record = TariffHistory.objects.filter(
                    user=tariff_history.user,
                    # tariff=tariff_history.tariff,
                    is_active=True
                    # TODO тут возможно в будущем пригодится фильтр еще и по Wave
                ).order_by("-valid_until").first()

                if is_first_payment:
                    # если первый платеж
                    if last_record:
                        # берем максимум, чтобы пользователь, который продлевает после паузы - начинал с сегодня,
                        # а не от старой даты конца подписки
                        tariff_history.valid_from = max(last_record.valid_until + timedelta(days=1), date.today())
                    else:
                        tariff_history.valid_from = date.today()
                else:
                    # если идет продление подписки, то всегда продлеваем встык
                    # иначе может получиться разрыв в днях из-зи нотификации после полуночи
                    # может использовать last_record, если идет продление, то текущая ТХ - подписка
                    tariff_history.valid_from = last_record.valid_until + timedelta(days=1)

                    # если последняя запись была "бонусом" для возможности внести деньга на карту, то
                    # деактивируем ее и сдвигаем время старта на заданные дни
                    days_diff = (last_record.valid_until - last_record.valid_from).days
                    if days_diff == settings.STRIPE_SUBSCRIPTION_PAST_DUE_DAYS - 1:

                        last_record.is_active = False
                        last_record.save(update_fields=['is_active'])

                        tariff_history.valid_from -= timedelta(days=settings.STRIPE_SUBSCRIPTION_PAST_DUE_DAYS)

                # обязательно нужно -1 от продолжительности, так проверки на активную запись ТХ идут <= valid_until.
                tariff_history.valid_until = tariff_history.valid_from + \
                    timedelta(days=tariff_history.tariff.duration_in_days - 1)

                # при первой оплате специально делаем на день больше, что было беспрерывный доступ
                if is_first_payment:
                    tariff_history.valid_until = tariff_history.valid_until + timedelta(days=1)

                else:
                    # если у нас случай перехода на подписку с триальной версией, то флаг первой оплаты не прийдет
                    # поэтому проверис была ли последняя оплата волновой или нет
                    if last_record.tariff.tariff_group.is_wave:
                        tariff_history.valid_until = tariff_history.valid_until + timedelta(days=1)

                tariff_history.save()

            stripe_subscription.subscription.status = Subscription.STATUS_ACTIVE
            stripe_subscription.subscription.save(update_fields=['status'])

        # нужно проверить статус подписки в страйте, если она не активна - то активировать,
        # иначе после неудачной оплаты она ставится в страйпе в past due, потом даже после оплаты не меняется и отменяется
        # специально вынес отдельно из-под атомика. Если упадет - кажется правильней, что доступ УЖЕ будет сразу
        # в нашей системе
        subscription = stripe.Subscription.retrieve(data.subscription)
        if subscription.cancel_at_period_end:
            stripe.Subscription.modify(
                data.subscription,
                cancel_at_period_end=False
            )

    except ObjectDoesNotExist:
        # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
        logger.error('Confirm subscription. Subscription_id not found %s', data.subscription)
    except Exception as e:
        logger.error('Confirm subscription. Subscription_id %s. Error = %s', data.subscription, e)


# отмена подписки
# используется в 2х местах, можно переписать немного потом, пока возврат результата добавлен
# для ручной отмены юзером ( для вывода ошибки на страницу)
def cancel_stripe_subscription(stripe_subscription_id, is_first_payment=False):
    try:
        stripe_subscription = StripeSubscription.objects.get(stripe_subscription_id=stripe_subscription_id)

        # страйп дает странную реакцию на попытку удалить уже отмененную подписку
        # валится с ошибкой и статусом 404. Обработаем через try-except
        try:
            # тестовая отмененная подписка (пока оставить для тестов)
            # subscription_id = 'sub_IUYwU4J2RExjEt'
            # Переписано на более лайтовое закрытие. Дает возможность переоткрывать подписку , менять ей план и тд
            stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True
            )

            if not is_first_payment:
                # не прошло продление , возможно нет денег на карте. У пользователя будет несколько дней,
                # чтобы пополнить и страйп будет пытаться списать еще не сколько раз.
                # Даем пользователю такую возможность, делаем небольшую ТХ с полным доступом по тарифу на это время
                user = stripe_subscription.subscription.user

                with transaction.atomic():

                    # Locking
                    Profile.objects.select_for_update().get(user=user)

                    last_record = TariffHistory.objects.filter(
                        user=user,
                        is_active=True
                    ).order_by("-valid_until").first()

                    days_diff = (last_record.valid_until - last_record.valid_from).days

                    # если разница больше чем заданный параметр - значит еще не создавали такую короткую ТХ
                    # проверка, что не волновая ТХ - если с подписки перешел на волновой, и уже есть ТХ на этот переход - короткая ТХ не нужна
                    # проверка на next_tariff_history - если осздали что-то руками или еще как-то, то не нужна короткая инче она сменит next_th и запись пропадет
                    if days_diff >= settings.STRIPE_SUBSCRIPTION_PAST_DUE_DAYS and not last_record.wave and not user.profile.next_tariff_history:

                        tariff_history = TariffHistory()
                        tariff_history.payment = None
                        tariff_history.tariff = last_record.tariff
                        tariff_history.user = user
                        tariff_history.is_active = True
                        tariff_history.wave = None

                        tariff_history.valid_from = last_record.valid_until + timedelta(days=1)

                        # обязательно нужно -1 от продолжительности, так проверки на активную запись ТХ идут <= valid_until.
                        tariff_history.valid_until = tariff_history.valid_from + \
                            timedelta(days=settings.STRIPE_SUBSCRIPTION_PAST_DUE_DAYS - 1)

                        tariff_history.save()

        except Exception as e:
            # определить по ошибке отменена ли уже подписка или же не существует такого айди в страйпе - нельзя, будем получать доп инфу
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            if subscription.canceled_at:
                # подписка уже отменена, продолжаем работу и выдаем пользователю сообщение что все ок
                pass
            else:
                # упала ошибка, подписка существует и не отменена, не можем продолжать работу, разбираемся
                raise Exception(e)

        # пока уберем, статус сменим в хуке по изменению подписки
        # if canceled:
        #     stripe_subscription.subscription.status = Subscription.STATUS_CANCELED
        #     stripe_subscription.subscription.save(update_fields=['status'])
        # else:
        #     # сюда можем зайти только, если метод страйпа по отмене не упал, но и вернул подписку не в отмененном статусе
        #     raise Exception('Stripe couldn"t delete the subscription.')

    except ObjectDoesNotExist:
        # если это первый платеж, то такой подписки еще нет в нашей БД, ничего не делаем, просто пропускаем мимо ушей.
        # Пользователь может попытаться еще раз оплатить (банально не верно введена карта, окно чекаута не закрывается)
        if is_first_payment:
            pass
        else:
            # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
            logger.error('Cancel subscription. Subscription_id not found %s', stripe_subscription_id)
            return False
    except Exception as e:
        # если упала какая-то еще ошибка - логируем
        logger.error('Cancel subscription. Subscription_id %s. Error = %s', stripe_subscription_id, e)
        return False

    return True


def modify_subscription(stripe_subscription_id, new_stripe_price):
    subscription = stripe.Subscription.retrieve(stripe_subscription_id)

    stripe.Subscription.modify(
        subscription.id,
        cancel_at_period_end=False,
        # payment_behavior='pending_if_incomplete',
        proration_behavior='none',
        items=[{
            'id': subscription['items']['data'][0].id,
            'price': new_stripe_price,
        }]
    )


def subscription_updating_failed(data):
    try:
        stripe_subscription = StripeSubscription.objects.get(stripe_subscription_id=data.stripe_id)

        msg = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=stripe_subscription.subscription.user.profile.telegram_id,
            text='Не удалось обновить режим подписки, пожалуйста, свяжитесь с командой проекта',
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )

        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    except ObjectDoesNotExist:
        # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
        capture_exception('subscription_updating_failed. Subscription_id not found %s', data.subscription)

    except Exception as e:
        capture_exception(e)


# обновили подписку (могли как улучшить так и ухудшить)
def subscription_updated(data):
    try:
        # данный эвэнт приходит и при создании подписки, его никак не выделить среди всех остальных
        # причем он еще приходит ДО всех событий (оплаты и тд), где мы проставляем айди из меты
        # поэтому будем делать все действия (включая отправку юзеру нотификации) только если была смена
        stripe_subscription = StripeSubscription.objects.filter(stripe_subscription_id=data.stripe_id).first()
        new_tariff = Tariff.objects.get(stripe_price_id=data.plan.id)

        if not stripe_subscription:
            return

        if stripe_subscription.subscription.tariff == new_tariff and \
                stripe_subscription.subscription.status != Subscription.STATUS_CANCELED:
            return

        with transaction.atomic():
            # Locking
            Profile.objects.select_for_update().get(user=stripe_subscription.subscription.user)
            # пока кажется, что вот этого достаточно, текущая ТХ не сменилась,
            # при след оплате возьмется новый тариф
            stripe_subscription.subscription.tariff = new_tariff
            stripe_subscription.subscription.status = Subscription.STATUS_ACTIVE
            stripe_subscription.subscription.save(update_fields=['tariff', 'status'])

        # вынесем логи и оповещения за атомик
        LogEntry.objects.log_action(
            user_id=settings.SYSTEM_USER_ID,
            content_type_id=ContentType.objects.get_for_model(stripe_subscription.subscription).pk,
            object_id=stripe_subscription.subscription.pk,
            object_repr=text(stripe_subscription.subscription.user.profile),
            action_flag=CHANGE,
            change_message="Change subscription plan"
        )

        msg = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=stripe_subscription.subscription.user.profile.telegram_id,
            text='Тарифный план подписки был успешно изменен',
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )

        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    except ObjectDoesNotExist:
        # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
        capture_exception('subscription_updated. Subscription_id not found %s', data.subscription)

    except Exception as e:
        capture_exception(e)


def subscription_canceled(data):
    try:
        stripe_subscription = StripeSubscription.objects.get(stripe_subscription_id=data.id)

        # если статус уже установлен в отмененную , то нет смысла его ставить и уведомлять пользователя
        # + отмену могут инициировать 2 эвэнта теперь , еще добавился deelted
        if stripe_subscription.subscription.status != Subscription.STATUS_CANCELED:
            stripe_subscription.subscription.status = Subscription.STATUS_CANCELED
            stripe_subscription.subscription.save(update_fields=['status'])

            user = stripe_subscription.subscription.user
            # Если в пределах срока, когда у всех открыта оплата,
            # участник сначала перешел на подписку, а потом решил отменить,
            # ему надо нормально вернуть возможность оплатить полную сумму
            # if user.profile.tariff_renewal_from and \
            #         user.profile.tariff_renewal_from <= date.today() <= user.profile.tariff_renewal_until:
            #     stripe_subscription.subscription.user.application.is_payment_allowed = True
            #     stripe_subscription.subscription.user.application.save(update_fields=['is_payment_allowed'])

            msg = DjangoTelegramBot.dispatcher.bot.send_message(
                chat_id=user.profile.telegram_id,
                text='Ваша подписка была отменена',
                disable_web_page_preview=True,
                parse_mode='Markdown',
                timeout=5
            )

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    except ObjectDoesNotExist:
        # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
        capture_exception('Canceled subscription. Subscription_id not found %s', data.id)
    except Exception as e:
        capture_exception(e)


def subscription_surcharged(data):
    try:
        stripe_subscription = StripeSubscription.objects.get(
            stripe_subscription_id=data.metadata.get('stripe_subscription_id'))
        new_tariff = Tariff.objects.get(slug=data.metadata.get('new_tariff'))

        user = stripe_subscription.subscription.user
        active_tariff = user.profile.active_tariff_history.tariff

        # определяем до чего апгрейдим ТХ и до чего апгрейдим подписку
        th_change_to = None
        subscription_change_to = None

        if is_upgrade(active_tariff, new_tariff):
            # тут всего один тариф - все изменеяем до него
            th_change_to = new_tariff
            subscription_change_to = new_tariff
        else:
            # в случае сайдгрейда разные смены
            th_change_to = Tariff.objects.get(slug=data.metadata.get('transition_tariff'))
            subscription_change_to = new_tariff

        with transaction.atomic():
            # сразу обновляем ТХ так как пропалата уже прошла и обновление в страйпе не должно влиять на текущий доступ

            # Locking
            Profile.objects.select_for_update().get(user=user)

            stripe_payment = StripePayment()
            stripe_payment.invoice_id = data.payment_intent  # обходимся тем что есть, это ссылка на платеж, где то на инвойс
            stripe_payment.save()

            payment = Payment()
            payment.user = user
            payment.tariff = th_change_to
            payment.payment_provider = 'Stripe'
            payment.payment_type = Payment.PAYMENT_TYPE_NON_WAVE
            payment.status = Payment.STATUS_APPROVED
            payment.amount = Decimal(data.amount_total) / 100
            payment.currency = data.currency.upper()
            payment.subscription = stripe_subscription.subscription
            payment.stripe_payment = stripe_payment
            payment.save()

            active_th = user.profile.active_tariff_history

            tariff_history = TariffHistory()
            tariff_history.payment = payment
            tariff_history.tariff = payment.tariff
            tariff_history.user = payment.user
            tariff_history.is_active = True
            tariff_history.wave = None  # TODO пока так, возможно потом придется менять
            tariff_history.valid_from = date.today()
            tariff_history.valid_until = active_th.valid_until
            tariff_history.save()

            active_th.valid_until = date.today() - timedelta(days=1)
            active_th.save(update_fields=['valid_until'])

        # уведомляем пользователя о том, что ему расширен текущий доступ
        msg = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=user.profile.telegram_id,
            text='Оплата прошла успешно и все выбранные вами опции активированы.',
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )

        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

        subscription = stripe.Subscription.retrieve(data.metadata.get('stripe_subscription_id'))

        # теперь нужно обновить подписку в страйпе
        # смену в бд сделаем в случае успешной смены в страйпе (через нотификацию)
        stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=False,
            proration_behavior='none',
            items=[{
                'id': subscription['items']['data'][0].id,
                'price': subscription_change_to.stripe_price_id,
            }]
        )

    except ObjectDoesNotExist:
        # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
        logger.error('Canceled subscription. Subscription_id not found %s', data.metadata.get('stripe_subscription_id'))
    except Exception as e:
        logger.error('Canceled subscription. Subscription_id %s. Error = %s',
                     data.metadata.get('stripe_subscription_id'), e)


def subscription_surcharged_failed(data):
    try:
        stripe_subscription = StripeSubscription.objects.get(stripe_subscription_id=data.stripe_id)

        msg = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=stripe_subscription.subscription.user.profile.telegram_id,
            text='Не удалось произвести доплату, если считаете что произошла ошбика - свяжитесь с командой проекта',
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )

        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    except ObjectDoesNotExist:
        # кидаем ошибку, вернем код 200, что обработали и нужно будет смотреть руками, что пошло не так и почему такого объекта нет
        capture_exception('subscription_surcharged_failed. Subscription_id not found %s', data.subscription)

    except Exception as e:
        capture_exception(e)


def make_stripe_payment(order, request):
    order.amount, order.currency = get_payment_amount(order)
    order.wave = get_payment_wave(request.user, tariff=order.tariff)

    if not order.payment_id:
        order.payment_id = str(uuid4())

    order.save()

    stripe_order_type_postfix = {
        'CHANNEL': 'Automated',
        'CHAT': 'Dedicated',
        'CLUB': 'Support'
    }

    if order.status == 'PROCESSING':
        return order, ''
    else:
        rates_list = get_vat_tax_rates()

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'EUR',
                    'product_data': {
                        'name': "Enrolment in the SELFREBOOTCAMP educational project (%s%s)" % (
                            stripe_order_type_postfix.get(order.payment_type),
                            ', Discount: %0.2f%%' % order.discount_code.dicount_percent if order.discount_code else '',
                        ),
                    },
                    'unit_amount': int(order.amount * 100),  # цена в центах
                },
                'quantity': 1,
                'dynamic_tax_rates': rates_list
            }],
            mode='payment',
            metadata={
                'payment_id': order.payment_id  # по этому ордеру будем идентифицировать инфу в вебхуках
            },
            success_url=request.build_absolute_uri(str(reverse('content:index-page'))),
            cancel_url=request.build_absolute_uri(str(reverse('crm:paywall-cancel'))),
        )
        return order, session.id


def make_pp_payment(order, request):
    order.amount, order.currency = get_payment_amount(order)
    order.wave = get_payment_wave(request.user, tariff=order.tariff)

    if not order.payment_id:
        order.payment_id = str(uuid4())

    order.save()

    paypal_order_type_postfix = {
        'CHANNEL': 'Automated',
        'CHAT': 'Dedicated',
        'CLUB': 'Support'
    }

    paypal_dict = {
        "business": settings.PAYPAL_BUSINESS_EMAIL,
        "amount": '%0.2f' % order.amount,
        "item_name": "Enrolment in the SELFREBOOTCAMP educational project (%s%s)" % (
            paypal_order_type_postfix.get(order.payment_type),
            ', Discount: %0.2f%%' % order.discount_code.dicount_percent if order.discount_code else '',
        ),
        "invoice": order.payment_id,
        "currency_code": 'EUR',
        "notify_url": request.build_absolute_uri(str(reverse('paypal:paypal-ipn'))),
        "return_url": request.build_absolute_uri(str(reverse('content:index-page'))),
        "cancel_return": request.build_absolute_uri(str(reverse('crm:paywall-cancel'))),
    }

    logger.info(paypal_dict)

    form = PayPalPaymentsForm(initial=paypal_dict)

    return order, form


def make_ya_payment(order, request, payment_method=None):
    order.amount, order.currency = get_payment_amount(order)
    order.wave = get_payment_wave(request.user, tariff=order.tariff)

    if not payment_method:
        payment_method = settings.RUSSIAN_PAYMENT_ALLOWED_METHODS['BANK_CARD']

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    if order.payment_provider in ['YA', 'YM']:
        payment_client = YandexPayment()
        payment_data = {
            'amount': {
                'value': '%0.2f' % order.amount,
                'currency': 'RUB'
            },
            'payment_method_data': {
                'type': payment_method,
            },
            'description': 'Оплата участия в программе для пользователя #%s (%s %s)%s' %
                           (
                               order.user.id,
                               order.user.application.first_name,
                               order.user.application.last_name,
                               ', Скидка: %0.2f%%' % order.discount_code.dicount_percent if order.discount_code else '',
            ),
            'receipt': {
                # 'phone': order.user.profile.mobile_number,
                # 'email': order.user.email,
                'items': [
                    {
                        'description': 'Участие в образовательной программе',
                        'quantity': 1,
                        'amount': {
                            'value': '%0.2f' % order.amount,
                            'currency': 'RUB'
                        },
                        'vat_code': 1,
                        'payment_subject': 'service',
                        'payment_mode': 'full_payment',
                    }
                ],
            },
            'confirmation': {
                'type': 'redirect',
                'return_url': settings.YANDEX_MONEY_RETURN_URL,
            },
            'capture': True,
            'client_ip': ip,
        }

        if order.user.profile.mobile_number:
            payment_data['receipt']['phone'] = order.user.profile.mobile_number

        if order.user.email:
            payment_data['receipt']['email'] = order.user.email

        if not payment_data['receipt'].get('email') and not payment_data['receipt'].get('phone'):
            return order

        logger.debug("Yandex Payment to create: %s" % payment_data)
        payment_order = payment_client.create(payment_data)
        logger.info("Yandex Payment created: %s" % vars(payment_order))

        order.payment_id = payment_order.id
        order.payment_url = payment_order.confirmation.confirmation_url
        order.status = 'PENDING'
        order.save()

        logger.info("Yandex Payment Order created: %s" % vars(order))
    else:
        raise NotImplemented()

    if order.amount == 0:
        order.status = 'APPROVED'
        order.save()

    return order


def get_payment_dates(user, tariff):
    # TODO: fix for switching between Wave and non-wave tariffs

    # оплата подписки в другой ветке, получается, что если зашли сюда - значит переходит на кампанию
    # с волной и просто возвращаем от нее
    if not user.profile.wave:
        # обязательно нужно -1 от продолжительности, так проверки на активную запись ТХ идут <= valid_until.
        return user.application.campaign.start_date, user.application.campaign.start_date + timedelta(
            days=tariff.duration_in_days - 1)

    if user.application.campaign.start_date > user.profile.valid_until:
        # если кампания начинается в будущем, то возвращаем от старта кампании
        # обязательно нужно -1 от продолжительности, так проверки на активную запись ТХ идут <= valid_until.
        return user.application.campaign.start_date, user.application.campaign.start_date + timedelta(
            days=tariff.duration_in_days - 1)
    else:
        # иначе - впритык (со следующего дня)
        # при продлении прибавляем продолжительность тарифа к окончанию прошлой хистори, -1 не нужен.
        return user.profile.valid_until + timedelta(1), user.profile.valid_until + timedelta(
            days=tariff.duration_in_days)


def get_payment_wave(user, tariff):
    # TODO: fix for switching between Wave and non-wave tariffs

    # Non-wave tariffs
    if not tariff.tariff_group.is_wave:
        return None

    # Wave tariffs
    # новый communication_mode будем получать из тарифа , так как пользователь может перейти из одного вида в другой
    communication_mode = tariff.tariff_group.communication_mode

    if user.application.campaign:
        # если у пользователя есть кампания, то берем из нее актуальный wave
        return user.application.campaign.wave_chat if communication_mode == 'CHAT' else user.application.campaign.wave_channel

    else:
        # если продление текущей кампании, то берем текущую волну
        return user.profile.wave


def build_order(user):
    order = Payment()
    order.user = user
    # if user.profile.communication_mode == 'CHAT':
    #     order.payment_provider = 'PP'
    if user.profile.tariff_next:
        order.tariff = user.profile.tariff_next
    order.payment_type = get_payment_type(user)

    if not order.payment_type:
        return None

    order.amount, order.currency = get_payment_amount(order)
    order.wave = get_payment_wave(user, tariff=order.tariff)

    order.save()

    return order


def confirm_order(order):
    """

    :param order:
    :type order: crm.models.Payment
    :return:
    """

    item = None
    stripe_subscription_id = None

    with transaction.atomic():
        # Locking
        Profile.objects.select_for_update().get(user=order.user)

        # Фикс для случая дублированной обработки ордера
        # если в тарифф хистори уже есть ссылка на этот ордер, то просто скипаем его
        if (TariffHistory.objects.filter(payment=order).exists()):
            # не будем заного сохранять все поля и уведомлять пользователя, просто возьмем заново ордер из базы
            order.refresh_from_db()
            return order

        order.status = 'APPROVED'
        if not order.paid_at:
            order.paid_at = localtime()

        fields_to_save = []

        if order.tariff:
            order.user.profile.tariff_next_id = None
            fields_to_save.append('tariff_next_id')

            # if not order.tariff.tariff_group.is_wave:
            #     order.user.profile.wave = None
            #     fields_to_save.append('wave')

        # if order.user.profile.wave_id:
        #     if order.wave_id and order.wave_id != order.user.profile.wave_id:
        #         order.user.profile.wave = order.wave
        #         fields_to_save.append('wave')
        # else:
        #     if not order.user.profile.is_in_club:
        #         if order.user.profile.communication_mode == 'CHAT':
        #             order.user.profile.wave = order.user.application.campaign.wave_chat
        #         if order.user.profile.communication_mode == 'CHANNEL':
        #             order.user.profile.wave = order.user.application.campaign.wave_channel

        # fields_to_save.append('wave')

        order.save(update_fields=['status', 'paid_at'])

        active_subscription_tariff_history = order.user.profile.active_tariff_history

        # надо так же заполнить тариф_хистори
        # заполнять надо только если был указан тариф
        if order.tariff:
            item = TariffHistory()
            item.payment = order
            item.tariff = order.tariff
            item.user = order.user
            item.is_active = True

            item.valid_from, item.valid_until = get_payment_dates(order.user, order.tariff)

            # вычисляем wave или берем из старой логики ? пока оставил новые вычисления
            item.wave = order.wave if order.tariff.tariff_group.is_wave else None

            item.save()

            # возможен случай, когда мы при активной подписке покупаем тариф
            if order.user.profile.active_subscription:
                prev_from_day = item.valid_from - timedelta(days=1)

                # нужно будет скорректировать ТХ данной подписки
                active_subscription_tariff_history.valid_from = min(
                    prev_from_day, active_subscription_tariff_history.valid_from)
                # тут получается, что можем подарить пользователю лишний доступ к подпискам.
                # скажем если подписка кончается 20ого числа, а старт тарифа волнового 25. Ставим тут до 24
                # согласовано с Шуром, считаем это подарком юзеру
                active_subscription_tariff_history.valid_until = prev_from_day
                active_subscription_tariff_history.save(update_fields=['valid_from', 'valid_until'])

        # order.user.profile.is_active = True
        # fields_to_save.append('is_active')

        order.user.profile.save(update_fields=fields_to_save)

        # order.user.application.is_payment_allowed = False
        # order.user.application.save(update_fields=['is_payment_allowed'])

    if item:
        active_subscription = order.user.profile.active_subscription

        if active_subscription:
            if active_subscription.stripe_subscription:
                cancelled = cancel_stripe_subscription(active_subscription.stripe_subscription.stripe_subscription_id)
                notify_user_by_telegram(record=item, cancelled=cancelled)

            else:
                cancel_yandex_subscription(subscription_id=active_subscription.pk)

        notify_user_by_telegram(record=item)

    return order


def validate_pp_order(sender, **kwargs):
    ipn_obj = sender
    logger.info(ipn_obj)
    logger.info(ipn_obj.__dict__)
    logger.info(ipn_obj.payment_status)
    logger.info(ipn_obj.invoice)
    logger.info(ipn_obj.mc_gross)
    logger.info(ipn_obj.mc_currency)

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        if ipn_obj.receiver_email != settings.PAYPAL_BUSINESS_EMAIL:
            # Not a valid payment
            return
        logger.info('EMAIL OK')

        existing_order = Payment.objects.filter(payment_id=ipn_obj.invoice).first()
        if not existing_order:
            return

        logger.info('Order found')
        logger.info('Amount: %0.2f' % existing_order.amount)

        if '%0.2f' % (ipn_obj.mc_gross - ipn_obj.tax) == '%0.2f' % existing_order.amount \
                and ipn_obj.mc_currency == 'EUR':
            logger.info('Confirming order')
            confirm_order(existing_order)

    if ipn_obj.payment_status == ST_PP_PENDING:
        if ipn_obj.receiver_email != settings.PAYPAL_BUSINESS_EMAIL:
            # Not a valid payment
            return

        existing_order = Payment.objects.filter(payment_id=ipn_obj.invoice).first()

        if not existing_order:
            return

        if '%0.2f' % (ipn_obj.mc_gross - ipn_obj.tax) == '%0.2f' % existing_order.amount \
                and ipn_obj.mc_currency == 'EUR':
            existing_order.status = 'PROCESSING'
            existing_order.save()


def fill_order_fields(sender: typing.Type[Payment], instance: Payment, **kwargs: typing.Dict) -> None:
    """

    :param sender:
    :param instance:
    :type instance: crm.models.Payment
    :param kwargs:
    :return:
    """
    if not instance.pk:
        if not instance.payment_provider:
            if instance.user.profile.communication_mode == 'CHAT':
                instance.payment_provider = 'PP'
            else:
                instance.payment_provider = 'YA'

        if not instance.payment_type:
            instance.payment_type = get_payment_type(instance.user)

        if not instance.tariff_id and instance.user.profile.tariff_next_id:
            instance.tariff_id = instance.user.profile.tariff_next_id

        if instance.amount is None or instance.currency is None:
            instance.amount, instance.currency = get_payment_amount(instance)

        if instance.wave is None:
            instance.wave = get_payment_wave(instance.user, tariff=instance.tariff)


def notify_user_by_telegram(record: TariffHistory, cancelled: bool = None) -> None:
    profile = record.user.profile

    profile.refresh_from_db()

    if not profile.telegram_id:
        return

    system_code = 'payment_confirmed'

    tpl = TGNotificationTemplate.objects.get(system_code=system_code)
    text = tpl.text.replace('END_DATE', '%s' % record.valid_until)

    try:
        msg = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=profile.telegram_id,
            text=text,
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )
    except Exception as exc:
        logger.exception(exc)
        return

    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    if cancelled is not None:
        # Отмена подписки прошла успешно, сообщаем об этом
        if cancelled:
            system_code = 'subscription_cancelled'
            tpl = TGNotificationTemplate.objects.get(system_code=system_code)

            try:
                msg = DjangoTelegramBot.dispatcher.bot.send_message(
                    chat_id=profile.telegram_id,
                    text=tpl.text,
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                    timeout=5
                )
            except Exception as exc:
                # кинем в сентри, чтобы ТОЧНО предупредить юзера в случае чего
                sentry_sdk.capture_exception(exc)
                return

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

        else:
            # отмена не удалась, кидаем в сентру
            sentry_sdk.capture_exception(Exception('Cancel subscription failed. user_id = %s', profile.user.pk))


valid_ipn_received.connect(validate_pp_order)
pre_save.connect(fill_order_fields, sender=Payment)
