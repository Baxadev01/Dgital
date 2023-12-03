# -*- coding: utf-8 -*-
import logging

import datetime
import sentry_sdk

from django.http.response import HttpResponseBadRequest, HttpResponseForbidden
from facebook import GraphAPI, GraphAPIError
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from rest_framework_tracking.mixins import LoggingMixin
from social_core.backends.google import GoogleOAuth2
from social_django.models import UserSocialAuth
from social_django.strategy import DjangoStrategy
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from srbc.apple_auth import AppleIdAppAuth
from srbc.models import Profile, User
from crm.models import Application
from srbc.serializers.general import ProfileSerializer, UserProfileSerializer
from swagger_docs import swagger_docs


logger = logging.getLogger('AUTH_API')

def create_user(email, username, uid, provider, user_data):
    user = User.objects.create_user(email=email, username=username)
    social_auth = UserSocialAuth(
        user_id=user.id,
        uid=uid,
        provider=provider,
        extra_data=user_data
    )

    social_auth.save()

    application = Application(user_id=user.id)
    application.save()

    profile = Profile(user_id=user.id, has_desktop_access=False)
    profile.save()

    return user
    

class AuthByFBToken(LoggingMixin, viewsets.ViewSet):
    permission_classes = (AllowAny,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/auth/facebook/']
    )
    def get_by_fb_token(request):
        """
            Aутентификация через Facebook аккаунт
        """

        fb_token = request.GET.get('token')

        if not fb_token:
            return HttpResponseBadRequest('token')

        graph = GraphAPI(access_token=fb_token)

        try:
            profile = graph.get_object("me")
        except GraphAPIError as e:
            return HttpResponseForbidden()

        # logger.debug(profile)

        fb_profile_id = profile.get('id')

        if not fb_profile_id:
            return HttpResponseForbidden('not_found')

        social_user = UserSocialAuth.objects.filter(provider='facebook', uid=fb_profile_id).first()

        if not social_user:
            return HttpResponseForbidden('not_found')

        if not social_user.user.profile.is_active:
            return HttpResponseForbidden('blocked')

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(social_user.user)
        jwt_token = jwt_encode_handler(payload)

        return Response({
            "token": jwt_token
        })


class AuthByAppleToken(LoggingMixin, viewsets.ViewSet):
    permission_classes = (AllowAny,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/auth/apple/']
    )
    def get_by_apple_token(request):
        """
            Aутентификация через Apple аккаунт
        """
        apple_token = request.GET.get('token')

        if not apple_token:
            return HttpResponseBadRequest('token')

        strategy = DjangoStrategy(storage=None)
        apple_oauth = AppleIdAppAuth(strategy=strategy)

        try:
            verified_token = apple_oauth.decode_app_token(id_token=apple_token)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return HttpResponseForbidden('bad_token')

        apple_user_id = verified_token.get('sub')

        if not apple_user_id:
            return HttpResponseForbidden('not_found')

        social_user = UserSocialAuth.objects.filter(provider='apple-id', uid=apple_user_id).first()

        if not social_user:
            return HttpResponseForbidden('not_found')

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
        **swagger_docs['GET /v1/register/apple/']
    )
    def register_by_apple_token(request):
        """
            Регистрация через Apple
        """
        apple_token = request.GET.get('token')

        if not apple_token:
            return HttpResponseBadRequest('token')

        strategy = DjangoStrategy(storage=None)
        apple_oauth = AppleIdAppAuth(strategy=strategy)

        try:
            verified_token = apple_oauth.decode_app_token(id_token=apple_token)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return HttpResponseForbidden('bad_token')

        apple_user_id = verified_token.get('sub')

        if not apple_user_id:
            return HttpResponseForbidden('bad token')

        social_user = UserSocialAuth.objects.filter(provider='apple-id', uid=apple_user_id).first()

        if social_user:
            return HttpResponseForbidden('already registered')

        # create_user(email, username, uid, provider):
        # FIXME!
        user = create_user('', '', apple_user_id, 'apple-id')

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(social_user.user)
        jwt_token = jwt_encode_handler(payload)

        return Response({
            "token": jwt_token
        })

class AuthByGoogleToken(LoggingMixin, viewsets.ViewSet):
    permission_classes = (AllowAny,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/auth/google/']
    )
    def get_by_google_token(request):
        """
            Aутентификация через Google аккаунт
        """
        google_token = request.GET.get('token')

        if not google_token:
            return HttpResponseBadRequest('token')

        strategy = DjangoStrategy(storage=None)
        google_oauth2 = GoogleOAuth2(strategy=strategy)

        try:
            user_data = google_oauth2.user_data(access_token=google_token)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return HttpResponseForbidden('bad_token')

        google_user_id = user_data.get('email')  
        
        if not google_user_id:
            return HttpResponseForbidden('not_found')

        social_user = UserSocialAuth.objects.filter(provider='google-oauth2', uid=google_user_id).first()

        if not social_user:
            return HttpResponseForbidden('not_found')

        if not social_user.user.profile.is_active:
            return HttpResponseForbidden('blocked')

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(social_user.user)
        jwt_token = jwt_encode_handler(payload)

        return Response({
            "token": jwt_token
        })

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/register/google/']
    )
    def register_by_google_token(request):
        """
            Регистрация через Google
        """
        google_token = request.GET.get('token')


        if not google_token:
            return HttpResponseBadRequest('token')

        strategy = DjangoStrategy(storage=None)
        google_oauth2 = GoogleOAuth2(strategy=strategy)

        try:
            user_data = google_oauth2.user_data(access_token=google_token)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return HttpResponseForbidden('bad_token')

        google_user_id = user_data.get('email')  
        
        if not google_user_id:
            return HttpResponseForbidden('bad token')

        social_user = UserSocialAuth.objects.filter(provider='google-oauth2', uid=google_user_id).first()

        if social_user:
            return HttpResponseForbidden('already registered')

        user = create_user(google_user_id, google_user_id.split('@')[0], google_user_id, 'google-oauth2', user_data)
    
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        jwt_token = jwt_encode_handler(payload)

        return Response({
            "token": jwt_token
        })


class CurrentUserViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects
    serializer_class = UserProfileSerializer

    @swagger_auto_schema(
        **swagger_docs['GET /v1/users/current/']
    )
    def get_current(self, *args, **kwargs):
        """
            Получение текущего пользователя
        """
        serialized = UserProfileSerializer(instance=self.request.user)
        return Response(serialized.data)


@method_decorator(name='get', decorator=swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/{id}/']
    ))
class ProfileItemViewSet(LoggingMixin, generics.ListAPIView):
    """ Получение пользователя  """

    permission_classes = (IsAuthenticated,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        if not self.request.user.is_staff:
            user_id = self.request.user.pk

        return self.queryset.filter(user__id=user_id)
