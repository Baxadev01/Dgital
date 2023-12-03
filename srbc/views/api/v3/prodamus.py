import datetime
from uuid import uuid4
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from django.urls import reverse
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict

from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from srbc.models import Profile, Subscription, StripeSubscription, Tariff
from crm.models import TariffHistory
from srbc.models.subscription import ProdamusSubscription
from crm.models.payments import Payment
from srbc.forms import ProdamusPaymentForm
from srbc.utils.permissions import HasStaffPermission

from sentry_sdk import capture_exception


class ProdamusPaymentAPIView(LoggingMixin, APIView):
    permission_classes = (HasStaffPermission,)

    @swagger_auto_schema(
        **swagger_docs['POST /api/v3/prodamus/payment/create/']
    )
    def post(self, request):
        """
            Создание ссылки для оплаты через Prodamus
        """

        form = ProdamusPaymentForm(request.POST)

        if form.is_valid():
            form = form.cleaned_data
            
        
            if form['user'].profile.is_blocked:
                
                return Response({'error': 'Этот пользователь заблокирован'})
            
            
            with transaction.atomic():
                    
                    # если нет wave, это значит что тариф по подписки
                    order = Payment()
                    order.payment_id = str(uuid4())
                    order.user = form['user']

                    if not form['wave']:

                        # # Для реализации рекурсивных платежей
                        # ps = ProdamusSubscription()
                        # ps.subscription_id = str(uuid4())
                        # ps.save()

                        subscription = Subscription()
                        subscription.status = Subscription.STATUS_NEW
                        subscription.tariff = form['tariff']
                        subscription.user = form['user']
                        # subscription.prodamus_subscription = ps
                        subscription.save()
                        order.subscription = subscription
                        

                    order.tariff = form['tariff']
                    order.payment_provider = 'PRODAMUS'
                    order.payment_type = form['tariff'].tariff_group.communication_mode
                    order.status = Payment.STATUS_PENDING
                    order.amount = form['price_rub']
                    order.currency = 'RUB'
                    order.wave = form['wave']
                    order.save()
                    
                    # Создаю TariffHistory ставлю просто is_active=False,
                    # потому что надо чтоб была возможность менять дату начала и конца из формы
                    # если платеж не пройдет удалю tariff_history
                    tariff_history = TariffHistory()
                    tariff_history.user = order.user
                    tariff_history.payment = order
                    tariff_history.tariff = order.tariff
                    tariff_history.is_active = False
                    tariff_history.wave = order.wave
                    tariff_history.valid_from = form['date_start']
                    tariff_history.valid_until = form['date_end']
                    tariff_history.save()

            if not form['wave']:
                product_name = 'Оформление подписки #%s (%s %s). \nТариф - %s' %(
                            order.user.id,
                            order.user.application.first_name,
                            order.user.application.last_name,
                            order.tariff.title,
                        )
            else: 
                product_name = 'Оплата участия в программе для пользователя #%s (%s %s)' % (
                            order.user.id,
                            order.user.application.first_name,
                            order.user.application.last_name,
                        )   

                    
            payment_data = {
                'order_id': order.payment_id,
                'do': 'pay',
                'products[0][name]': product_name,
                'products[0][price]': order.amount,
                'products[0][quantity]': 1,
                'sys': settings.PRODAMUS_SYS_CODE,
                'customer_phone': order.user.profile.mobile_number,
                'urlNotification': f'https://{request.get_host()}/prodamus-notifications/'
            }

            dict = QueryDict(mutable=True)
            dict.update(payment_data)
            url_payment_page = settings.PRODAMUS_DOMAIN_PAYMENT_PAGE

            

            return Response({'url': f'https://{url_payment_page}?{dict.urlencode()}'})
        else:
             return Response({'error': 'Неправильно заполнена форма'})

