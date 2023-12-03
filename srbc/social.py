# -*- coding: utf-8 -*-
import hashlib
import hmac
import logging
from time import time

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from social_core.backends.base import BaseAuth
from social_core.exceptions import AuthFailed, AuthMissingParameter
from social_core.exceptions import AuthForbidden, AuthAlreadyAssociated
from social_core.utils import handle_http_errors

from crm.models import Application
from srbc.models import Profile

USER_FIELDS = ['username', 'email']

ALLOWED_REGISTER_BACKENDS = ['facebook', 'telegram', 'google-oauth2', 'apple-id']
SAFE_REGISTER_BACKENDS = ['telegram', ]
ALLOWED_SIGNIN_BACKENDS = ['facebook', 'apple-id', 'telegram', 'google-oauth2']

logger = logging.getLogger(__name__)


def social_user(backend, uid, user=None, *args, **kwargs):
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)

    # телеграм в своих методах устанавливает backend и у него auth параметр уходит в data
    auth_action = backend.strategy.session_get('auth') or backend.data.get('auth')
    # ветка только для попытки логина
    if auth_action == 'login':

        # проверка на наличие акка в нашей системе
        if not social:
            msg = 'Account not found.'
            raise AuthFailed(backend, msg)

        user = social.user
        
        # тут НЕЛЬЗЯ давать вход если регался в мобильной аппке
        if not user.profile.has_desktop_access:
            redirect('/')

    # эта ветка для привязка акка 
    elif auth_action == 'connect':
        # по сути если есть social - это значит у нас в БД есть уже такая почта
        # уже кажется немного странным, но оставим такую сложную проверку (раз она была)
        if social:
            if user and social.user != user:
                msg = 'This {0} account is already in use.'.format(provider)
                raise AuthAlreadyAssociated(backend, msg)

    # эта ветка для создания нового акка
    else:
        if provider not in ALLOWED_SIGNIN_BACKENDS:
            raise AuthForbidden(backend)

        # если уже есть такой юзер - не даем заного
        if social:
            msg = 'You already have registered account'
            raise AuthFailed(backend, msg)

        # FIXME ? может быть такой случай, что social и user None. Но при этом почта (для гугла) может быть у юзера уже
        # возможно это чисто в моей бд (много удалял и правил), но мб нет

    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': social is None}


def save_profile(backend, user, response, strategy, *args, **kwargs):
    try:
        profile = Profile.objects.get(user=user)
    except ObjectDoesNotExist:
        profile = Profile(user_id=user.id)

    try:
        application = Application.objects.get(user=user)
    except ObjectDoesNotExist:
        application = Application(user_id=user.id)
        application.save()

    if profile.wave and not application.is_approved:
        application.is_approved = True
        application.save()

    # profile.telegram_join_code = uuid.uuid4()
    # while Profile.objects.filter(telegram_join_code=profile.telegram_join_code).exists():
    #     profile.telegram_join_code = uuid.uuid4()

    profile.save()


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}
    elif backend.name not in ALLOWED_REGISTER_BACKENDS:
        return redirect('/')
    elif not strategy.session_get('social_registration_allowed_%s' % backend.name) \
            and backend.name not in SAFE_REGISTER_BACKENDS:
        return redirect('/')

    fields = dict((name, kwargs.get(name, details.get(name)))
                  for name in backend.setting('USER_FIELDS', USER_FIELDS))
    if not fields:
        return redirect('/')

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }


def get_ig_user_data(username):
    """ Простой способ получить данные по аккаунту из инстаграма.

    :param username: 
    :type username: str
    :rtype: dict
    """
    import requests
    import re
    from bs4 import BeautifulSoup
    import json

    resp = requests.get('https://www.instagram.com/%s/' % username)
    soup = BeautifulSoup(resp.text, 'html.parser')

    if not resp.ok:
        # либо 404, либо не работает инстаграмм
        return None

    for script in soup.findAll('script'):
        data = script.string
        p = re.compile('window._sharedData = (.*?);')
        m = p.match(data)
        if m:
            try:
                user_info = json.loads(m.groups()[0])
                user_data = user_info['entry_data']['ProfilePage'][0]['graphql']['user']
            except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                # что-то изменили в инстаграме
                return None
            return user_data

    # что-то изменили в инстаграме
    return None


class TelegramAuth(BaseAuth):
    name = 'telegram'
    ID_KEY = 'id'

    def verify_data(self, response):
        bot_token = self.setting('BOT_TOKEN')
        if bot_token is None:
            raise AuthMissingParameter('telegram',
                                       'SOCIAL_AUTH_TELEGRAM_BOT_TOKEN')

        received_hash_string = response.get('hash')
        auth_date = response.get('auth_date')

        if received_hash_string is None or auth_date is None:
            raise AuthMissingParameter('telegram', 'hash or auth_date')

        data_check_string = ['{}={}'.format(k, v)
                             for k, v in response.items() if k not in ['hash','auth']]
        data_check_string = '\n'.join(sorted(data_check_string))
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        built_hash = hmac.new(secret_key,
                              msg=data_check_string.encode(),
                              digestmod=hashlib.sha256).hexdigest()
        current_timestamp = int(time())
        auth_timestamp = int(auth_date)
        if current_timestamp - auth_timestamp > 86400:
            raise AuthFailed('telegram', 'Auth date is outdated')
        if built_hash != received_hash_string:
            raise AuthFailed('telegram', 'Invalid hash supplied')

    def extra_data(self, user, uid, response, details=None, *args, **kwargs):
        return response

    def get_user_details(self, response):
        first_name = response.get('first_name', '')
        last_name = response.get('last_name', '')
        fullname = '{} {}'.format(first_name, last_name).strip()
        return {
            'username': response.get('username') or response[self.ID_KEY],
            'first_name': first_name,
            'last_name': last_name
        }

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        response = self.data
        self.verify_data(response)
        kwargs.update({'response': self.data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)
