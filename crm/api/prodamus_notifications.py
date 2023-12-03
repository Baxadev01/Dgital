import logging

from django.conf import settings
from datetime import timedelta
from django_telegrambot.apps import DjangoTelegramBot
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication 
from drf_yasg.utils import swagger_auto_schema

from django.utils.timezone import localtime

from content.utils import store_dialogue_reply
from crm.utils.prodamus_hmac import HmacProdamus, normalize_dict
from crm.models import TariffHistory
from crm.utils.payments import notify_user_by_telegram, cancel_stripe_subscription
from crm.utils.yandex_subscription import cancel_yandex_subscription
from crm.models.payments import Payment, ProdamusPayment
from srbc.models.subscription import Subscription
from swagger_docs import swagger_docs


logger = logging.getLogger(__name__)

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class ProdamusNotificationsAPIView(LoggingMixin, APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (CsrfExemptSessionAuthentication,)

    
    @swagger_auto_schema(
        **swagger_docs['POST /prodamus-notifications/']
    )
    def post(self, request):
        """
            Метод для получения уведомлений об оплате с Prodamus
        """
        
        sign = request.headers.get('Sign')
        prodamus_secret_key = settings.PRODAMUS_SECRET_KEY

        request_dict = normalize_dict(request.POST.dict())


        # Проверка подписи
        if not HmacProdamus.verify(prodamus_secret_key, request_dict, sign):
            return Response(status=400)
        
        payment_id = request_dict.get('order_num')
        if not payment_id:
                logger.error(
                        'ProdamusNotificationsAPIView. request without order_num. order_id = %s',
                        request_dict.get('order_id'))
                return Response(status=400)
        
        order = Payment.objects.filter(payment_id=payment_id).first()
        if not order:
            logger.error(
                'ProdamusNotificationsAPIView.  unknown payment_id. order_id = %s, payment_id=%s',
                request_dict.get('order_id'), payment_id)
            return Response(status=400)
        
        if request_dict.get('sum') != '%0.2f' % order.amount:
            logger.error(
                'ProdamusNotificationsAPIView. The amount paid by the client does not match the amount of payment. order_id = %s, payment_id=%s',
                request_dict.get('order_id'), payment_id)
            print('ProdamusNotificationsAPIView. The amount paid by the client does not match the amount of payment. order_id = %s, payment_id=%s',
                request_dict.get('order_id'), payment_id)
            return Response(status=400)
        
        
        if(request_dict.get('payment_status') == 'success'):
        
            item = None
            
            with transaction.atomic():
                if (TariffHistory.objects.filter(payment=order, is_active=True).exists()):
                    # не будем заного сохранять все поля и уведомлять пользователя, просто возьмем заново ордер из базы
                    order.refresh_from_db()
                    return Response(status=200)
                
                prodamus_payment = ProdamusPayment()
                prodamus_payment.invoice_id = request_dict.get('order_id')
                prodamus_payment.save()
                
                order.status = 'APPROVED'
                order.prodamus_payment = prodamus_payment
                if not order.paid_at:
                    order.paid_at = localtime()
                
                fields_to_save = []
                
                if order.tariff:
                    order.user.profile.tariff_next_id = None
                    fields_to_save.append('tariff_next_id')

                active_subscription = order.user.profile.active_subscription

                if active_subscription:
                    if active_subscription.stripe_subscription:
                        cancelled = cancel_stripe_subscription(active_subscription.stripe_subscription.stripe_subscription_id)
                        notify_user_by_telegram(record=item, cancelled=cancelled)
                    else:
                        cancel_yandex_subscription(subscription_id=active_subscription.pk)

                
                if not order.wave:
                    order.subscription.status = Subscription.STATUS_ACTIVE
                    order.subscription.save(update_fields=['status'])

                
                order.user.profile.save(update_fields=fields_to_save)

                order.save(update_fields=['status', 'paid_at', 'prodamus_payment'])

                active_tariff_history = order.user.profile.active_tariff_history

                item = TariffHistory.objects.filter(payment=order).first()
                item.is_active = True
                item.save(update_fields=['is_active'])
                
                # Если есть активный tariff_history, то если он пересекается с текущим корректируем дату окончания предыдущего
                if active_tariff_history:
                    prev_from_day = item.valid_from - timedelta(days=1)

                    # нужно будет скорректировать ТХ данной подписки
                    active_tariff_history.valid_from = min(
                        prev_from_day, active_tariff_history.valid_from)
                    # тут получается, что можем подарить пользователю лишний доступ к подпискам.
                    # скажем если подписка кончается 20ого числа, а старт тарифа волнового 25. Ставим тут до 24
                    # согласовано с Шуром, считаем это подарком юзеру
                    active_tariff_history.valid_until = prev_from_day
                    active_tariff_history.save(update_fields=['valid_from', 'valid_until'])


            notify_user_by_telegram(record=item)

        else:
            # Если пользователь отменил подписку

            item = TariffHistory.objects.filter(payment=order).first()
            item.delete()
            
            order.status = Payment.STATUS_CANCELED
            order.save(update_fields=['status'])

            if not order.wave:
                order.subscription.status = Subscription.STATUS_CANCELED
                order.subscription.save(update_fields=['status'])

                # Если в пределах срока, когда у всех открыта оплата,
                # участник сначала перешел на подписку, а потом решил отменить,
                # ему надо нормально вернуть возможность оплатить полную сумму
                # if user.profile.tariff_renewal_from and \
                #         user.profile.tariff_renewal_from <= date.today() <= user.profile.tariff_renewal_until:
                #     stripe_subscription.subscription.user.application.is_payment_allowed = True
                #     stripe_subscription.subscription.user.application.save(update_fields=['is_payment_allowed'])

            msg = DjangoTelegramBot.dispatcher.bot.send_message(
                chat_id=order.user.profile.telegram_id,
                text='Ваша платеж был отменен',
                disable_web_page_preview=True,
                parse_mode='Markdown',
                timeout=5
            )

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

        
        return Response(status=200)


        


