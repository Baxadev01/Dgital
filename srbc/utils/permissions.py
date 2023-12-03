# -*- coding: utf-8 -*-
from datetime import date

from rest_framework import permissions, exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from srbc.models import TariffGroup
from srbc.utils.auth import check_mobile_version


class JSONWebTokenMobileAuthentication(JSONWebTokenAuthentication):
    def authenticate(self, request):
        if not check_mobile_version(request.headers['User-Agent']):
            raise exceptions.AuthenticationFailed(
                'Эта версия приложения устарела. Пожалуйста, обновите приложение для продолжения работы.')

        return super(JSONWebTokenAuthentication, self).authenticate(request)


class HasStaffPermission(permissions.BasePermission):
    """
        Allows access only to authenticated users with stuff permission.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsActiveUser(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.profile.is_active
        )


class IsWaveUser(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.profile.wave
            and request.user.profile.valid_until
            and request.user.profile.valid_until >= date.today() >= request.user.profile.wave.start_date
        )


class HasMeetingAccess(permissions.BasePermission):
    """
    Allows access to meetings
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and base_tariff_permissons(request.user)
            and request.user.profile.tariff.tariff_group.meetings_access != TariffGroup.MEETINGS_NO_ACCESS
        )


class HasDiaryReadAccess(permissions.BasePermission):
    """
    Allows access to read diary records
    """

    # пока даем доступ на чтение всем, флаг NO_ACCESS убрали
    def has_permission(self, request, view):
        return bool(
            request.user
            # and base_tariff_permissons(request.user)
        )


class HasDiaryWriteAccess(permissions.BasePermission):
    """
    Allows access to save diary records
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and base_tariff_permissons(request.user)
            and request.user.profile.tariff.tariff_group.diary_access != TariffGroup.DIARY_ACCESS_READ
        )


class HasKnowledgeBaseAccess(permissions.BasePermission):
    """
    Allows access to knowledge base
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and base_tariff_permissons(request.user)
            and request.user.profile.tariff.tariff_group.kb_access
        )


class HasExpertiseAccess(permissions.BasePermission):
    """
    Allows access to expertise methods
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and base_tariff_permissons(request.user)
            and request.user.profile.tariff.tariff_group.expertise_access
        )


class IsValidUser(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.profile.is_active
            and request.user.profile.valid_until
            and request.user.profile.wave
            and request.user.profile.valid_until >= date.today()
        )


def base_tariff_permissons(user):
    return bool(
        user.profile.valid_until
        and user.profile.valid_until >= date.today()
        and user.profile.tariff
    )


def check_user_id(request, user_id):
    """ Анализирует запрос. Проверяет корректность переданного user_id.
    Получает user_id из request-a, если необходимо.

    :param request:
    :type request: django.core.handlers.wsgi.WSGIRequest
    :param user_id: идентификатор пользователя из запроса
    :type user_id: str
    :return: вернет id пользователя, если все ок (если user_id некорректный, то вернет None)
    :rtype: int | None
    """
    if user_id and user_id != str(request.user.pk):
        if request.user.is_staff:
            return int(user_id)
        else:
            return None
    else:
        return request.user.pk
