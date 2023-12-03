# -*- coding: utf-8 -*-
import re
from copy import deepcopy
from django.conf import settings
from rest_framework_jwt.settings import DEFAULTS, IMPORT_STRINGS, APISettings

from django.contrib.auth.models import User

from srbc.models import TariffGroup


class ProgressBar:
    login = {}
    names = {}
    username = {}
    tariff = {}
    campaign = {}
    application = {}
    telegram = {}
    admission = {}
    payment = {}
    # instagram = {}

    order = [
        login,
        names,
        username,
        telegram,
        application,
        tariff,
        admission,
        payment,
        # instagram,
    ]

    user = None
    current_slug = None

    def __init__(self, user, current_slug):
        # type: (User, str) -> None
        self.user = user
        self.current_slug = current_slug
        self.data_init()
        self.process_user()
        self.set_current_route()

    def data_init(self):
        self.login.update({
            "slug": "login",
            "title": "Регистрация",
            "url": "/welcome/",
            "is_current": True,
            "is_active": True,
            "is_passed": False,
            "is_visible": True,
        })

        self.names.update({
            "slug": "names",
            "title": "Знакомство",
            "url": "/names/?change=1",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        self.username.update({
            "slug": "username",
            "title": "Имя пользователя",
            "url": "/username/",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        self.tariff.update({
            "slug": "tariff",
            "title": "Тариф и дата&nbsp;старта",
            "url": "/tariff/",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        self.campaign.update({
            "slug": "campaign",
            "title": "",
            "url": "/wave/",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        self.application.update({
            "slug": "application",
            "title": "Анкета",
            "url": "/application/",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        self.telegram.update({
            "slug": "telegram",
            "title": "Телефон и чатбот",
            "url": "/telegram/",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        self.admission.update({
            "slug": "admission",
            "title": "Тестирование",
            "url": "/admission/",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        self.payment.update({
            "slug": "payment",
            "title": "Активация",
            "url": "/payment/",
            "is_current": False,
            "is_active": False,
            "is_passed": False,
            "is_visible": True,
        })

        # self.instagram.update({
        #     "slug": "instagram",
        #     "title": u"Подключение Instagram",
        #     "url": "/instagram/",
        #     "is_current": False,
        #     "is_active": False,
        #     "is_passed": False,
        #     "is_visible": False,
        # })

    def process_user(self):
        try:
            user_profile = self.user.profile
            user_application = self.user.application

            self.login['is_passed'] = True
            self.login['is_active'] = False
            self.names['is_active'] = True

            if user_application.first_name and user_application.last_name:
                self.names['is_passed'] = True
                self.username['is_active'] = True

            if not self.user.profile.username_is_editable:
                self.username['is_passed'] = True
                self.telegram['is_active'] = True

            if self.telegram['is_active'] and user_profile.telegram_id:
                self.telegram['is_passed'] = True
                self.telegram['is_active'] = False
                self.application['is_active'] = True

            try:
                self.application['is_passed'] = user_application.birth_year is not None
            except User.application.RelatedObjectDoesNotExist:
                self.application['is_passed'] = False

            if self.application['is_passed']:
                self.tariff['is_active'] = True

            if self.tariff['is_active'] and user_application.tariff and user_application.campaign:
                self.tariff['is_passed'] = True
                self.admission['is_active'] = True

            if user_application.tariff.tariff_group.communication_mode == TariffGroup.COMMUNICATION_MODE_CHAT:
                self.admission['is_visible'] = False

                if self.admission['is_active']:
                    self.payment['is_active'] = True
                else:
                    self.payment['is_active'] = False
            else:
                self.admission['is_visible'] = True

                try:
                    self.admission['is_passed'] = self.user.admission_test.status in [
                        'ACCEPTED', 'DONE', 'PASSED',
                        'FAILED',
                    ]

                    self.admission['is_failed'] = self.user.admission_test.status in ['REJECTED']

                    self.payment['is_active'] = self.user.admission_test.status in ['ACCEPTED']

                except User.admission_test.RelatedObjectDoesNotExist:
                    self.admission['is_passed'] = False

            if user_profile.is_active and user_profile.active_tariff_history.wave_id:
                self.tariff['is_active'] = False
                self.payment['is_passed'] = True
                self.payment['is_active'] = False
                # self.instagram['is_active'] = True
        except AttributeError:
            pass

    def set_current_route(self):
        for e in self.order:
            if e['slug'] == self.current_slug:
                e['is_current'] = True
                # e['is_active'] = True
            else:
                e['is_current'] = False

    def can_be_here(self):
        for e in self.order:
            if e['slug'] == self.current_slug:
                return e['is_active']

        return False

    def route(self):
        return [e for e in self.order if e['is_visible']]


def check_mobile_version(user_agent):
    # проверка пришедшего в хедерах User-Agent на минимальную версию
    if not user_agent:
        return False

    pattern = re.compile(r"^SRBC Mobile App - (?P<device>.*) - (?P<version>.*)[\+](?P<build>[0-9]+)$")
    result = pattern.match(user_agent)

    if not result:
        # если пришло с веб-страницы - формат не совпал
        return True

    build = result.group("build")

    if int(build) < settings.ACTUAL_MOBILE_BUILD:
        return False

    return True


def get_short_time_jwt(user, duration=None):
    local_user_settings = deepcopy(settings.JWT_AUTH)
    local_user_settings['JWT_EXPIRATION_DELTA'] = duration or settings.QR_JWT_EXPIRATION_DELTA

    api_settings = APISettings(local_user_settings, DEFAULTS, IMPORT_STRINGS)

    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    jwt_token = jwt_encode_handler(payload)

    return jwt_token


def get_deeplink(token):
    return "%s?token=%s" % (settings.MOBILE_DEEPLINK, token)
