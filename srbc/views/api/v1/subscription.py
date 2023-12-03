from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from crm.utils.yandex_subscription import cancel_yandex_subscription
from crm.utils.payments import cancel_stripe_subscription

# создает чекаут для разовой оплаты апгрейда/сайдшрейда подписки
class SubscriptionCancel(LoggingMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        **swagger_docs['POST /v1/subscription/cancel/']
    )
    def post(self, request):
        """
            Отменить подписку
        """
        try:
            active_subscription = request.user.profile.active_subscription

            if(not active_subscription):
                return Response({'error': "No active subscription"})

            if active_subscription.stripe_subscription:
                canceled = cancel_stripe_subscription(
                    stripe_subscription_id=active_subscription.stripe_subscription.stripe_subscription_id)

                if not canceled:
                    return Response({'error': "Can't cancel this subscription"})
            
            else:
                cancel_yandex_subscription(subscription_id=active_subscription.pk)

            return Response({'Запрос отправлен, о результате мы уведомим вас в телеграме'})
        except Exception as e:
            capture_exception(e)
            return Response({'error': 'Произошла ошибка, попробуйте, пожалуйста, позже'})
