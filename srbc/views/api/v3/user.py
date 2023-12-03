import sentry_sdk
from rest_framework.viewsets import ViewSet
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.response import Response
from django.http.response import HttpResponseBadRequest, HttpResponseForbidden
from rest_framework.permissions import AllowAny
from social_django.strategy import DjangoStrategy
from social_django.models import UserSocialAuth
from drf_yasg.utils import swagger_auto_schema
from rest_framework_jwt.settings import api_settings
from django.utils.decorators import method_decorator
from srbc.social import TelegramAuth
from social_django.models import UserSocialAuth
from srbc.models import Profile, User
from crm.models import Application

from swagger_docs import swagger_docs


def create_user(username, uid, provider, first_name, last_name):
    user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name)
    social_auth = UserSocialAuth(
        user_id=user.id,
        uid=uid,
        provider=provider,
        extra_data={
        }
    )

    social_auth.save()

    application = Application(user_id=user.id)
    application.save()

    profile = Profile(user_id=user.id, has_desktop_access=False)
    profile.save()

    return user

class AuthByTelegram(LoggingMixin, ViewSet):
    permission_classes = (AllowAny,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v3/auth/telegram/']
    )
    def get_by_telegram(request):
        """
            Аутентификация через Telegram аккаунт
        """ 

        strategy = DjangoStrategy(storage=None)
        telegram_auth = TelegramAuth(strategy=strategy)
        
        try:
            telegram_auth.verify_data(request.GET)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return HttpResponseBadRequest('Bad request')
        
        uid = request.GET.get('id')
        
        social_user = UserSocialAuth.objects.filter(uid=uid, provider='telegram').first()

        if not social_user:
            return HttpResponseForbidden('Пользователь не зарегистрирован')
        
        # if not social_user.user.profile.is_active:
        #     return HttpResponseForbidden('blocked')

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(social_user.user)
        jwt_token = jwt_encode_handler(payload)

        return Response({
            "token": jwt_token
        })
        

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v3/register/telegram/']
    )
    def register_by_telegram(request):
        """
            Регистрация через Telegram
        """

        strategy = DjangoStrategy(storage=None)
        telegram_auth = TelegramAuth(strategy=strategy)
        
        try:
            telegram_auth.verify_data(request.GET)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return HttpResponseBadRequest('Bad request')
        
        uid = request.GET.get('id')
        username = request.GET.get('username')
        last_name = request.GET.get('last_name', '')
        first_name = request.GET.get('first_name', '')

        social_user = UserSocialAuth.objects.filter(uid=uid, provider='telegram').exists()

        if social_user:
            return HttpResponseBadRequest('Пользователь yжe зарегистрирован')

        social_user = User.objects.filter(username=username).exists()
        if social_user:
            return HttpResponseBadRequest(f'Имя пользователя {username} уже используется')
        
        user = create_user(username, uid, 'telegram', first_name, last_name)

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        jwt_token = jwt_encode_handler(payload)

        return Response({
            "token": jwt_token
        })

