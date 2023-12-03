# -*- coding: utf-8 -*-
import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from social_core import exceptions as social_exceptions
from social_django.middleware import SocialAuthExceptionMiddleware

from srbc.models import Profile


class LoginUnderMiddleware(MiddlewareMixin):
    # def __init__(self, get_response):
    #     self.get_response = get_response
    #     # One-time configuration and initialization.
    #
    # def __call__(self, request):
    #     # Code to be executed for each request before
    #     # the view (and later middleware) are called.
    #     response = self.get_response(request)
    #     # Code to be executed for each request/response after
    #     # the view is called.
    #     return response

    def process_request(self, request):
        impersonation_allowed = False
        user_groups = request.user.groups.values_list('name', flat=True)
        login_under_user = request.user

        if request.user.is_superuser or 'Customer Manager' in user_groups:
            impersonation_allowed = True

        if impersonation_allowed and "__login_under" in request.GET:
            _login_under = request.GET.get("__login_under", 0)
            try:
                request.session['under_user_id'] = int(_login_under)
            except (ValueError, TypeError):
                pass
        elif "__logout_under" in request.GET:
            if (impersonation_allowed or request.user.is_superuser) and 'under_user_id' in request.session:
                del request.session['under_user_id']

        if impersonation_allowed and 'under_user_id' in request.session:
            try:
                login_under_user = User.objects.get(id=request.session['under_user_id'])
                # No one is allowed to login under a superuser
                if not login_under_user.is_superuser:
                    request.user = login_under_user
                return
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass


class TimezoneMiddleware(MiddlewareMixin):
    # TODO: need new middleware methods  (call and init) ?
    def process_request(self, request):
        try:
            if request.user.is_authenticated and request.user.profile and request.user.profile.timezone:
                timezone.activate(pytz.timezone(request.user.profile.timezone))
            else:
                timezone.deactivate()
        except Profile.DoesNotExist:
            timezone.deactivate()


class UserRelatedMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user and request.user.is_authenticated:
            request.user = User.objects.select_related(
                'profile__active_tariff_history__tariff__tariff_group',
                'profile__active_tariff_history__wave',
                'profile__next_tariff_history__tariff__tariff_group',
                'profile__next_tariff_history__wave',
                'application__tariff__tariff_group'
            ).get(pk=request.user.pk)


def debug_callback(request):
    return request.user.pk == 1
    # return request.user.is_authenticated() and request.user.is_superuser


# TODO протестить, видел пост о том, что все самописные middleware должны наследоваться от MiddlewareMixin
# верхние 2 наследуются, этот нет, в сеттингах прописан
class SRBCSocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    # TODO: need new middleware methods  (call and init) ?
    def process_exception(self, request, exception):
        url = self.get_redirect_uri(request, exception)

        if isinstance(exception, social_exceptions.AuthCanceled):
            # отменили авторизацию из соц. сети
            message = 'Авторизация отменена пользователем.'
            messages.error(request, message)
            return redirect(url)
        elif isinstance(exception, social_exceptions.AuthStateMissing):
            # `state` отсутствует в сессии (например, начинали авторизацию в одном браузере,
            # а попытались из другого браузера пройти по ссылке, которую генерит ФБ после авторизации)
            message = 'Что-то пошло не так. Пожалуйста, убедитесь, что Вы находитесь в том же браузере,' \
                      ' из которого начали авторизацию и попробуйте снова.'
            messages.error(request, message)
            return redirect(url)
        elif isinstance(exception, social_exceptions.AuthStateForbidden):
            # `state` отсутствует в сессии (например, начинали авторизацию в одном браузере,
            # а попытались из другого браузера пройти по ссылке, которую генерит ФБ после авторизации)
            message = 'Что-то пошло не так. Пожалуйста, убедитесь, ' \
                      'что приложение SelfRebootCamp в Facebook не заблокировано вами.'
            messages.error(request, message)
            return redirect(url)

    def get_redirect_uri(self, request, exception):
        return settings.SOCIAL_AUTH_LOGIN_ERROR_URL
