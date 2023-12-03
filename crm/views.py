# -*- coding: utf-8 -*-
import json
import stripe
import logging
import ipaddress

from django.conf import settings
from django.http import HttpResponse

#Yandex checkout doesn't work anymore
#from yandex_checkout import Configuration, WebhookNotification, \
#    WebhookNotificationEventType, Payment as YandexPayment

#yookassa is the new payment module
from yookassa import Configuration, Payment as YandexPayment
from yookassa.domain.notification import WebhookNotification, WebhookNotificationEventType

from sentry_sdk import capture_event, capture_exception

from .models import Payment
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from crm.utils.payments import update_stripe_subscription_id, \
    confirm_stripe_subscription_payment, cancel_stripe_subscription, subscription_canceled, \
    confirm_yandex_payment, cancel_yandex_payment, subscription_updating_failed, \
    subscription_updated, subscription_surcharged, subscription_surcharged_failed, \
    confirm_order

from crm.utils.yandex_subscription import confirm_subscription_payment, yandex_subscription_payment_failed
from srbc.decorators import has_desktop_access

Configuration.configure(settings.YANDEX_MONEY_SHOP_ID, settings.YANDEX_MONEY_SHOP_PASSWORD)

logger = logging.getLogger(__name__)


@login_required
@has_desktop_access
def payment_cancel(request):
    if request.user.application.active_payment_order:
        if request.user.application.active_payment_order.discount_code:
            request.user.application.active_payment_order.discount_code.is_applied = False
            request.user.application.active_payment_order.discount_code.save()

        request.user.application.active_payment_order.status = 'CANCELED'
        request.user.application.active_payment_order.save()

    return redirect('/payment/')


# Webhooks are always sent as HTTP POST requests, so ensure
# that only POST requests reach your webhook view by
# decorating `webhook()` with `require_POST`.
#
# To ensure that the webhook view can receive webhooks,
# also decorate `webhook()` with `csrf_exempt`.
# @require_POST
@csrf_exempt
def stripe_notify_view(request):
    # To acknowledge receipt of an event, your endpoint must return a 2xx HTTP status code to Stripe.
    # All response codes outside this range, including 3xx codes, indicate to Stripe that you did not receive the event.

    # If Stripe does not receive a 2xx HTTP status code, the notification attempt is repeated.
    # After multiple failures to send the notification over multiple days, Stripe marks the event as failed
    # and stops trying to send it to your endpoint. After multiple days without receiving any 2xx HTTP status code responses,
    # Stripe emails you about the misconfigured endpoint, and automatically disables your endpoint soon after if unaddressed.

    # Because properly acknowledging receipt of the webhook notification is so important, your endpoint should return a 2xx HTTP
    # status code prior to any complex logic that could cause a timeout.

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_KEY
        )

        # для тесто черех CLI - раскомментить эту строку + убрать преобразования через подпись выше
        # event = stripe.Event.construct_from(
        #     json.loads(payload), stripe.api_key
        # )

    except ValueError as e:
        # Invalid payload
        logger.error('stripe_notify_view. Invalid payload! Error = %s', e)
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error('stripe_notify_view. Invalid signature!! Error = %s', e)
        return HttpResponse(status=400)

    data = event.data.object

    # FIXME тесты, удалить/закомментить перед заливкой
    # создание подписки
    # data.subscription = "sub_INOVpk5fSPZXKn"
    # data.mode = "subscription"
    # data.metadata.subscription_id = "30db1fc6-457a-44d0-bbd8-3bba801ba8e9"

    # возвращаем 200 везде -> Обработали запрос, внутри каждой функции кидаем raise/выводим в лог и потом разбираемся, что случилось.
    # возвращать 400 и повторно слать не вижу пока смысла нигде, нужно анализировать, что идет не так, потом
    # потом можно обернуть тут все в трай кетч - и в случае raise внутри методов - добавлять реакцию (по необходимости)

    # есть "промежуточные действия", которые генерят эвэнты. Это позволяет на них не реагировать
    # is_fake = data.metadata.get('fake_event', None)
    # if is_fake:
    #     return HttpResponse(status=200)

    # может вернуться как для разового платежа так и при создании подписки
    if event.type == 'checkout.session.completed':
        # если mode установлен в подписку - значит тут подтверждение создания подписки
        if data.mode == "subscription":
            update_stripe_subscription_id(data)
        else:
            # отдельно нужно обработать режим изменения подписки
            if data.metadata.get('change_subscription'):
                subscription_surcharged(data)

            # тут обрабатываем обычный платеж
            else:
                payment_id = data.metadata.get('payment_id')
                if not payment_id:
                    logger.error(
                        'stripe_notify_view. checkout.session.completed event without payment_id. event_id = %s',
                        data.id)
                    return HttpResponse(status=400)
                else:
                    order = Payment.objects.filter(payment_id=payment_id).first()
                    if not order:
                        logger.error(
                            'stripe_notify_view. checkout.session.completed event, payment mode, unknown payment_id. event_id = %s, payment_id=%s',
                            data.id, payment_id)
                        return HttpResponse(status=400)
                    else:
                        if event.data.object.payment_status == "paid":
                            confirm_order(order)
                        else:
                            # не удалось сделать не paid, поэтмоу пока оставим лог и все.
                            # обрабатывать другие события нет смысла, если оплата не прошла, то ошибка остается на странице страйпа
                            # и он дает еще попытки, пока не пройдет оплата.
                            logger.error(
                                'stripe_notify_view. checkout.session.completed event, payment mode, wrong payment status. event_id = %s, payment_id=%s, payment_status=%s',
                                data.id, payment_id, event.data.object.payment_status)
                            return HttpResponse(status=400)
                            # cancel_payment(order)

    elif event.type == 'invoice.paid':
        # нас интересует для обработки только случай, когда операция с подпиской
        # может быть как продление так и новая
        # проверка на "subscription_update" - чтобы событие доплаты за подписку обрабатывали в отдельном эвэнте
        if data.subscription and data.billing_reason != "subscription_update":
            # проверим это автоплатеж или создание подписки
            is_first_payment = data.billing_reason == 'subscription_create'

            confirm_stripe_subscription_payment(data, is_first_payment=is_first_payment)

    elif event.type == 'invoice.payment_failed':
        # проверяем что подписка
        if data.subscription:
            if data.metadata.get('change_subscription'):
                subscription_surcharged_failed(data)
            else:
                # проверим это автоплатеж или создание подписки
                # проверка на "subscription_update" - чтобы событие доплаты за подписку обрабатывали в отдельном эвэнте
                is_first_payment = data.billing_reason == 'subscription_create'
                cancel_stripe_subscription(stripe_subscription_id=data.subscription, is_first_payment=is_first_payment)

    elif event.type == 'customer.subscription.updated':
        # отмену подписки пока сделали более мягкой, с возможностью восстановить и апгрейднуть/даунгрейднуть
        # поэтому проверяем так
        if data.cancel_at_period_end:
            subscription_canceled(data)
        elif data.pending_update:
            # если пришло данное поле, то обновление не удалось
            subscription_updating_failed(data)
        else:
            # если null, то обновление удалось
            subscription_updated(data)
    elif event.type == 'customer.subscription.deleted':
        subscription_canceled(data)

    return HttpResponse(status=200)


@csrf_exempt
def yandex_kassa_notify_view(request):
    # проверить на подлинность можно 2 способами
    # 1 - проверка IP

    # получаем ip
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    ip_address = ipaddress.ip_address(ip)

    allowed = next((ip for ip in settings.YANDEX_NOTIFICATIONS_ALLOWED_IPS
                    if ip_address in ipaddress.ip_network(ip)), None)

    if not allowed:
        # scam
        # выводим в лог и бунтуем
        logger.error('Not allowed ip address %s', ip)
        capture_exception(Exception('Not allowed ip address %s', ip))
        return HttpResponse(status=400)

    event_json = json.loads(request.body)
    try:
        notification_object = WebhookNotification(event_json)
    except Exception as exc:
        capture_exception(exc)
        return HttpResponse(status=400)

    # 2 - проверка текущего статуса объекта
    payment_object = YandexPayment.find_one(str(notification_object.object.id))
    if not payment_object:
        # чет странное пришло
        capture_exception(Exception('payment not found, id = %s', str(notification_object.object.id)))
        return HttpResponse(status=400)

    # проверяем, что все корректно со статусом платежа
    if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
        # подтверждение платежа. Проверяем статус
        if payment_object.status == 'succeeded':
            # здесь конфирмим плтеж в БД

            yandex_subscription_id = notification_object.object.metadata.get('subscription_id', None)
            if yandex_subscription_id:
                confirm_subscription_payment(notification_object.object)
            else:
                confirm_yandex_payment(notification_object.object)

            return HttpResponse(status=200)
        else:
            # чет не то
            capture_exception('Wrong payment status! PAYMENT_SUCCEEDED! payment status = %s', payment_object.status)
            return HttpResponse(status=400)

    elif notification_object.event == WebhookNotificationEventType.PAYMENT_CANCELED:
        # отмена платежа. Проверяем статус
        if payment_object.status == 'canceled':
            # здесь отменяем платеж в БД
            yandex_subscription_id = notification_object.object.metadata.get('subscription_id', None)
            if yandex_subscription_id:
                yandex_subscription_payment_failed(notification_object.object)
            else:
                cancel_yandex_payment(notification_object.object)
            return HttpResponse(status=200)

        else:
            # чет не то
            capture_exception('Wrong payment status! PAYMENT_CANCELED! payment status = %s', payment_object.status)
            return HttpResponse(status=400)

    return HttpResponse(status=200)
