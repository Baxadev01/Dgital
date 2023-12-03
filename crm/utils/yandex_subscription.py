from uuid import uuid4
from datetime import timedelta, date

from django.conf import settings
from django.db import transaction
from django_telegrambot.apps import DjangoTelegramBot
from django.core.exceptions import ObjectDoesNotExist

from content.utils import store_dialogue_reply

from crm.models import YandexPayment as  YandexPaymentModel, Payment, TariffHistory
from content.models import TGNotificationTemplate
from srbc.models import Tariff, Subscription, YandexSubscription

#Yandex checkout doesn't work anymore
#from yandex_checkout import Configuration, WebhookNotification, \
#    WebhookNotificationEventType, Payment as YandexPayment
#from yandex_checkout.domain.common.payment_method_type import PaymentMethodType as PaymentMethod

#yookassa is the new payment module
from yookassa import Configuration, Payment as YandexPayment
from yookassa.domain.notification import WebhookNotification, WebhookNotificationEventType
from sentry_sdk import capture_event, capture_exception

Configuration.configure(settings.YANDEX_MONEY_SHOP_ID, settings.YANDEX_MONEY_SHOP_PASSWORD)

# создание чекаута для подписки яндекса
# пока try вынесен вверхний уровень
def create_first_subscription_payment(user, tariff):
    ys = YandexSubscription()
    # пока его просто генерим, а потом в нотификациях заменим на айди от страйпа
    ys.subscription_id = str(uuid4())
    ys.save()

    subscription = Subscription()
    subscription.status = Subscription.STATUS_NEW
    subscription.tariff = tariff
    subscription.user = user
    subscription.yandex_subscription = ys
    subscription.save()

    payment_client = YandexPayment()
    payment_data = {
        'amount': {
            'value': '%0.2f' % tariff.fee_rub,
            'currency': 'RUB'
        },
        'payment_method_data': {
            'type': settings.RUSSIAN_PAYMENT_ALLOWED_METHODS['BANK_CARD'], # FIXME можно подумать про всякие другие методы потом
        },
        # FIXME
        'description': 'Оформление подписки #%s (%s %s). \nТариф - %s' %
                    (
                        user.id,
                        user.application.first_name,
                        user.application.last_name,
                        tariff.title,
        ),
        # FIXME
        'receipt': {
            # 'phone': order.user.profile.mobile_number,
            # 'email': order.user.email,
            'items': [
                {
                    'description': 'Оформление подписки',
                    'quantity': 1,
                    'amount': {
                        'value': '%0.2f' % tariff.fee_rub,
                        'currency': 'RUB'
                    },
                    'vat_code': 1,
                    'payment_subject': 'service',
                    'payment_mode': 'full_payment',
                }
            ],
        },
        'metadata' : {
            'subscription_id': ys.subscription_id  # по этому ордеру будем идентифицировать инфу в вебхуках
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': settings.YANDEX_MONEY_RETURN_URL,
        },
        'capture': True,
        # 'client_ip': ip, #пока убрал, не вижу зачем он нужен
        "save_payment_method": True
    }

    if user.profile.mobile_number:
        payment_data['receipt']['phone'] = user.profile.mobile_number

    if user.email:
        payment_data['receipt']['email'] = user.email

    if not payment_data['receipt'].get('email') and not payment_data['receipt'].get('phone'):
        # кинем ошибку, пользователю выведется стандартный текст о том, что "произошла ошибка"
        raise

    payment_order = payment_client.create(payment_data)
    return payment_order

def extending_subscription(subscription):
    try:
        tariff = subscription.tariff
        user = subscription.user
        payment_data = {
            'amount': {
                'value': '%0.2f' % tariff.fee_rub,
                'currency': 'RUB'
            },
            "payment_method_id":  subscription.yandex_subscription.yandex_payment_id,
            'description': 'Продление подписки #%s (%s %s). \nТариф - %s' %
                        (
                            user.id,
                            user.application.first_name,
                            user.application.last_name,
                            tariff.title,
            ),
             'receipt': {
                # 'phone': order.user.profile.mobile_number,
                # 'email': order.user.email,
                 'items': [
                     {
                         'description': 'Продление подписки',
                         'quantity': 1,
                         'amount': {
                             'value': '%0.2f' % tariff.fee_rub,
                             'currency': 'RUB'
                         },
                         'vat_code': 1,
                         'payment_subject': 'service',
                         'payment_mode': 'full_payment',
                     }
                 ],
             },
            'metadata' : {
                'subscription_id': subscription.yandex_subscription.subscription_id  # по этому ордеру будем идентифицировать инфу в вебхуках
            },
            'capture': True,
        }
        if user.profile.mobile_number:
            payment_data['receipt']['phone'] = user.profile.mobile_number

        if user.email:
            payment_data['receipt']['email'] = user.email

        if not payment_data['receipt'].get('email') and not payment_data['receipt'].get('phone'):
            # кинем ошибку, пользователю выведется стандартный текст о том, что "произошла ошибка"
            raise
        payment_client = YandexPayment.create(payment_data)

    except Exception as e:
        capture_exception(e)

def confirm_subscription_payment(payment_object):
    # получили нотификацию о конфирме

    try:
        payment_object = YandexPayment.find_one(str(payment_object.id))

        yandex_subscription_id = payment_object.metadata.get('subscription_id', None)
        change_sub = payment_object.metadata.get('modify', False)

        if not yandex_subscription_id:
            raise('confirm_subscription_payment. yandex_subscription_id not found')

        subscription = Subscription.objects.get(yandex_subscription__subscription_id=yandex_subscription_id)

        if change_sub:
            # TODO - ветка грейдов не реализована, просто заложена
            pass
        else:
            if '%0.2f' % payment_object.amount.value != '%0.2f' % subscription.tariff.fee_rub:
                raise('confirm_subscription_payment. Strange payment amount')

            with transaction.atomic():
                yandex_payment = YandexPaymentModel()
                yandex_payment.invoice_id = payment_object.id
                yandex_payment.save()

                payment = Payment()
                payment.user = subscription.user
                # подписка всегда в рамках одного тарифа
                payment.tariff = subscription.tariff
                payment.payment_provider = 'YA'
                payment.payment_type = Payment.PAYMENT_TYPE_NON_WAVE
                payment.status = Payment.STATUS_APPROVED
                payment.amount = payment_object.amount.value
                payment.currency = payment_object.amount.currency
                payment.subscription = subscription
                payment.yandex_payment = yandex_payment
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
                    is_active=True
                ).order_by("-valid_until").first()

                is_first_payment = subscription.status == Subscription.STATUS_NEW

                if is_first_payment:
                    # если первый платеж
                    if last_record:
                        # берем максимум, чтобы пользователь, который продлевает после паузы - начинал с сегодня,
                        # а не от старой даты конца подписки
                        tariff_history.valid_from = max(last_record.valid_until + timedelta(days=1), date.today())
                    else:
                        tariff_history.valid_from = date.today()

                    # Для первого платежа ОБЯЗАТЕЛЬНО надо сохранить payment_method

                    subscription.yandex_subscription.yandex_payment_id = payment_object.payment_method.id
                    subscription.yandex_subscription.save(update_fields=['yandex_payment_id'])

                else:
                    # если идет продление подписки, то всегда продлеваем встык
                    # иначе может получиться разрыв в днях из-зи нотификации после полуночи
                    # может использовать last_record, если идет продление, то текущая ТХ - подписка
                    tariff_history.valid_from = last_record.valid_until + timedelta(days=1)


                # обязательно нужно -1 от продолжительности, так проверки на активную запись ТХ идут <= valid_until.
                tariff_history.valid_until = tariff_history.valid_from + \
                    timedelta(days=tariff_history.tariff.duration_in_days - 1)

                if last_record and last_record.tariff.tariff_group.is_wave:
                    tariff_history.valid_until = tariff_history.valid_until + timedelta(days=1)

                    subscription.user.profile.tariff_next = None
                    subscription.user.profile.save(update_fields=['tariff_next'])

                tariff_history.save()

                # пока не стал выносить за атомик, но в целом мб надо
                subscription.status = Subscription.STATUS_ACTIVE
                subscription.save(update_fields=['status'])


            if subscription.user.profile.telegram_id:

                if is_first_payment:
                    tpl = TGNotificationTemplate.objects.get(system_code='yandex_new_subscription')
                    text = tpl.text.replace('TARIFF', '%s' % subscription.tariff.title)
                    text = text.replace('NEXT_PAYMENT_DATE', '%s' % tariff_history.valid_until)
                else:
                    tpl = TGNotificationTemplate.objects.get(system_code='yandex_extending_subscription')
                    text = tpl.text.replace('NEXT_PAYMENT_DATE', '%s' % tariff_history.valid_until)

                msg = DjangoTelegramBot.dispatcher.bot.send_message(
                    chat_id=subscription.user.profile.telegram_id,
                    text=text,
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                    timeout=5
                )

                store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)


    except Subscription.DoesNotExist as e:
        capture_exception('confirm_subscription_payment. Subscription_id not found %s', yandex_subscription_id)

    except Exception as e:
        capture_exception(e)


# Отменяет подписку по одному из айди
def cancel_yandex_subscription(subscription_id=None, yandex_subscription_id=None):
    try:
        if subscription_id:
            subscription = Subscription.objects.get(pk=subscription_id)
        else:
            subscription = Subscription.objects.get(yandex_subscription__subscription_id=yandex_subscription_id)

        if subscription.status != Subscription.STATUS_CANCELED:
            not_first_payment = subscription.status == Subscription.STATUS_ACTIVE

            subscription.status = Subscription.STATUS_CANCELED
            subscription.save(update_fields=['status'])

            subscription.yandex_subscription.yandex_payment_id = None
            subscription.yandex_subscription.save(update_fields=['yandex_payment_id'])

            # надо понять первый ли это платеж, если нет - то надо уведомить
            if not_first_payment and subscription.user.profile.telegram_id:

                tpl = TGNotificationTemplate.objects.get(system_code='yandex_cancel_subscription')
                text = tpl.text.replace('END_DATE', '%s' % subscription.user.profile.active_tariff_history.valid_until)

                msg = DjangoTelegramBot.dispatcher.bot.send_message(
                    chat_id=subscription.user.profile.telegram_id,
                    text=text,
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                    timeout=5
                )

                store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    except ObjectDoesNotExist:
        capture_exception('cancel_yandex_subscription. Subscription_id not found')
    except Exception as e:
        capture_exception(e)


# обработка события о неудачном платеже за подписку
def yandex_subscription_payment_failed(payment_object):
    # не прошел платеж, отменяем подписку, если она в статусе ACTIVE
    # yandex_subscription_id = payment_object.metadata.get('subscription_id', None)
    yandex_subscription_id = YandexPayment.find_one(str(payment_object.id)).metadata.get('subscription_id', None)

    if not yandex_subscription_id:
        raise('yandex_subscription_payment_failed. yandex_subscription_id not found')

    cancel_yandex_subscription(yandex_subscription_id = yandex_subscription_id)
