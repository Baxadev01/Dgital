from re import sub
import stripe
import datetime
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.http.response import HttpResponseBadRequest

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from crm.utils.payments import modify_subscription
from crm.utils.subscription import is_sidegrade, is_upgrade, is_downgrade, get_changing_surcharge

from srbc.models import Profile, Subscription, StripeSubscription, Tariff
from srbc.utils.stripe import get_vat_tax_rates

from sentry_sdk import capture_exception

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)


class StripeSubscriptionCheckout(LoggingMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        **swagger_docs['POST /v1/stripe/subscription/create/checkout/']
    )
    def post(self, request):
        """
            Оформить подписку
        """
        tariff_slug = request.data.get('tariff', None)
        # мб стоит вместо None сделать settings.STRIPE_DEFAULT_TARIFF

        if request.user.profile.active_subscription:
            return Response({'error': 'У вас уже есть активная подписка'})

        try:
            tariff = Tariff.objects.get(slug=tariff_slug)

            if request.user.profile.active_subscription:
                return Response({'error': "У вас уже есть активная подписка"})

            if request.user.profile.next_tariff_history:
                return Response(
                    {'error': "Невозможно оформить подписку в данный момент, так как вы уже продлили участие в проекте"})

            subscription_data = {}
            active_th = request.user.profile.active_tariff_history
            if active_th and active_th.wave:

                first_sub_day = active_th.valid_until + datetime.timedelta(days=1)
                trial_days = (first_sub_day - datetime.date.today()).days - 1

                # !! на тестовых данных иногда неправильно отображается чекаут. Пишет вместо 21 день триала - 1 день триал,
                # но при этом потом в подписке все корректно..  не знаю с чем свзяано, при это 20, 22, 23 - корректно, 58 или 59 - нет....
                if trial_days > 0:
                    subscription_data['trial_period_days'] = trial_days

            rates_list = get_vat_tax_rates()

            # создаем подписку тут сразу и передадим ее в метадату
            ss = StripeSubscription()
            # пока его просто генерим, а потом в нотификациях заменим на айди от страйпа
            ss.subscription_id = str(uuid4())
            ss.save()

            subscription = Subscription()
            subscription.status = Subscription.STATUS_NEW
            subscription.tariff = tariff
            subscription.user = request.user
            subscription.stripe_subscription = ss
            subscription.save()

            # success_url и cancel_url пока как в пейменте
            checkout_session = stripe.checkout.Session.create(
                success_url=request.build_absolute_uri(str(reverse('content:index-page'))),
                cancel_url=request.build_absolute_uri(str(reverse('crm:paywall-cancel'))),
                payment_method_types=["card"],
                mode="subscription",
                line_items=[
                    {
                        "price": tariff.stripe_price_id,
                        "quantity": 1,
                        'dynamic_tax_rates': rates_list
                    }
                ],
                metadata={
                    'subscription_id': ss.subscription_id  # по этому ордеру будем идентифицировать инфу в вебхуках
                },
                subscription_data=subscription_data
            )

            return Response({'sessionId': checkout_session['id']})
        except ObjectDoesNotExist:
            # пока не используется по сути, возможно пригодится при выборе тарифа
            return Response({'error': "Wrong slug"})
        except Exception as e:
            capture_exception(e)
            return Response({'error': 'Произошла ошибка, попробуйте, пожалуйста, позже'})


class StripeSubscriptionChange(LoggingMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        **swagger_docs['POST /v1/stripe/subscription/change/']
    )
    def post(self, request):
        """
            Сменить тариф
        """
        tariff_slug = request.data.get('tariff', None)

        try:
            new_tariff = Tariff.objects.get(slug=tariff_slug)
            active_th = request.user.profile.active_tariff_history
            active_subscription = request.user.profile.active_subscription

            if(not active_subscription):
                return Response({'error': "No active subscription"})

            # отдельно вынесем случай, если пользователь меняет свою подписку после сайдчейна
            # в ТХ у него будет более "продвинутый тариф" до конца месяца.
            # Если новый тариф свопадает с ТХ, то по сути работает аналогично даунгрейду
            if active_th.tariff != active_subscription.tariff:
                if active_th.wave:
                    # если активен волновой тариф - значит меняем подписку в будущем, просто модифаем, доплаты не нужны.
                    modify_subscription(active_subscription.stripe_subscription.stripe_subscription_id,
                                        new_tariff.stripe_price_id)
                    return Response({'Запрос отправлен, о результате мы уведомим вас в телеграме'})

                if active_th.tariff == new_tariff:
                    # случай сайдгрейда, где на месяц оплатили более продвинутую и потом меняют будущий тариф
                    modify_subscription(active_subscription.stripe_subscription.stripe_subscription_id,
                                        new_tariff.stripe_price_id)
                    return Response({'Запрос отправлен, о результате мы уведомим вас в телеграме'})

            # вычислять доплату и нужна ли она должны от текущего тарифа в ТХ. В случае сайдгрейда - тут более продвинутый тариф
            # и если опльзователь решит еще раз его сменить, то доплатить должен сразу на основании ТХ
            active_tariff = active_th.tariff

            # по сути этой проверкой сразу отсечем все оставшееся, что не требует чекаута, а требует просто смены
            if is_downgrade(active_tariff, new_tariff):
                modify_subscription(active_subscription.stripe_subscription.stripe_subscription_id,
                                    new_tariff.stripe_price_id)
                return Response({'Запрос отправлен, о результате мы уведомим вас в телеграме'})
                # return Response({'error': "Wrong data"})

            metadata = {}
            sidegrade, transition = is_sidegrade(active_tariff, new_tariff)
            if sidegrade:
                transition_tariff = Tariff.objects.get(slug=transition)
                amount = round(get_changing_surcharge(
                    active_tariff, transition_tariff, active_th.valid_until, datetime.date.today()), 2)
                metadata['change_subscription'] = 'sidegrade'
                metadata['transition_tariff'] = transition

            else:
                amount = round(get_changing_surcharge(
                    active_tariff, new_tariff, active_th.valid_until, datetime.date.today()), 2)
                metadata['change_subscription'] = 'upgrade'

            metadata['new_tariff'] = new_tariff.slug
            metadata['stripe_subscription_id'] = active_subscription.stripe_subscription.stripe_subscription_id

            # слишком маленькая доплата, дарим пользователю
            if amount < 1:
                modify_subscription(active_subscription.stripe_subscription.stripe_subscription_id,
                                    new_tariff.stripe_price_id)
                text = "Запрос отправлен, доплата не потребуется. О результате мы уведомим вас в телеграме"
                return Response({text})

            # здесь только создадим инвойс, данные будем менять после нотификации о результате
            # success_url и cancel_url пока как в пейменте
            rates_list = get_vat_tax_rates()
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'EUR',
                        'product_data': {  # FIXME - поправить имя
                            'name': "Доплата за смену тарифа",  # FIXME
                        },
                        'unit_amount': int(amount * 100),  # цена в центах
                    },
                    'quantity': 1,
                    'dynamic_tax_rates': rates_list
                }],
                mode='payment',
                metadata=metadata,
                success_url=request.build_absolute_uri(str(reverse('content:index-page'))),
                cancel_url=request.build_absolute_uri(str(reverse('crm:paywall-cancel'))),
            )

            return Response({'sessionId': checkout_session['id']})
        except ObjectDoesNotExist:
            # пока не используется по сути, возможно пригодится при выборе тарифа
            return Response({'error': "Wrong tariff"})
        except Exception as e:
            capture_exception(e)
            return Response({'error': 'Произошла ошибка, попробуйте, пожалуйста, позже'})
