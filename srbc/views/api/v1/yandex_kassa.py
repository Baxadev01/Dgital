from django.core.exceptions import ObjectDoesNotExist
from sentry_sdk import capture_exception

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from crm.utils.yandex_subscription import create_first_subscription_payment
from srbc.models import Tariff

class YandexSubscriptionCreate(LoggingMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        **swagger_docs['POST /v1/yandex/subscription/create/checkout/']
    )
    def post(self, request):
        """
            Оформить подписку через Yandex
        """
        tariff_slug = request.data.get('tariff', None)

        try:
            tariff = Tariff.objects.get(slug=tariff_slug)

            if request.user.profile.active_subscription:
                return Response({'error': "У вас уже есть активная подписка"})

            if request.user.profile.next_tariff_history:
                return Response(
                    {'error': "Невозможно оформить подписку в данный момент, так как вы уже продлили участие в проекте"})

            payment_order = create_first_subscription_payment(request.user, tariff)
            return Response({'payment_url': payment_order.confirmation.confirmation_url})
   
        except ObjectDoesNotExist:
            # пока не используется по сути, возможно пригодится при выборе тарифа
            return Response({'error': "Wrong slug"})
        except Exception as e:
            capture_exception(e)
            return Response({'error': 'Произошла ошибка, попробуйте, пожалуйста, позже'})

