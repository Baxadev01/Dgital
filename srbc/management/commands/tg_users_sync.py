# -*- coding: utf-8 -*-
from builtins import str as text

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType

from srbc.models import User
from datetime import date
import requests
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Loads TG user info"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        user_id = options.get('user', None)
        today = date.today()
        users = User.objects.filter(
            tariff_history__valid_until__gte=today,
            tariff_history__valid_from__lte=today,
            tariff_history__is_active=True,
            tariff_history__tariff__tariff_group__is_wave=True,
            profile__telegram_id__isnull=False,
            # profile__communication_mode='CHANNEL'
        ).select_related('profile')

        if user_id:
            users = users.filter(pk=user_id)

        users = users.all()

        tg_url_tpl = 'https://api.telegram.org/bot%s/getChatMember?chat_id=%s&user_id=%s'
        bot_key = '321197722:AAF-9GQ0hlrHoboNAQ3bzI36e-ZLf5ybcks'

        for _user in users:
            # print "=" * 50
            # print "User: %s" % _user.pk
            # print "=" * 50

            userchats = _user.membership.all()
            _profile = _user.profile
            first_name = None
            last_name = None

            for _chat in userchats:
                chat_id = _chat.chat.tg_id

                if not chat_id:
                    continue

                tg_data_url = tg_url_tpl % (
                    bot_key,
                    chat_id,
                    _profile.telegram_id,
                )

                response = requests.get(tg_data_url)

                if response.status_code == 400:
                    continue

                tg_data = response.json()

                # print tg_data

                if not first_name:
                    first_name = tg_data.get('result', {}).get('user', {}).get('first_name')

                if not last_name:
                    last_name = tg_data.get('result', {}).get('user', {}).get('last_name')

                chat_status = tg_data.get('result', {}).get('status')
                old_status = _chat.status
                if chat_status == 'kicked':
                    _chat.status = 'BANNED'

                if chat_status in ['member', 'creator', 'administrator']:
                    _chat.status = 'JOINED'

                if chat_status == 'left':
                    if chat_status == 'JOINED':
                        _chat.status = 'LEFT'
                    else:
                        _chat.status = 'ALLOWED'
                if _chat.status != old_status:
                    _chat.save()

                    if _chat.status == 'BANNED':
                        LogEntry.objects.log_action(
                            user_id=settings.SYSTEM_USER_ID,
                            content_type_id=ContentType.objects.get_for_model(_chat).pk,
                            object_id=_chat.pk,
                            object_repr=text(_chat.user.profile),
                            action_flag=CHANGE,
                            change_message="tg_users_sync"
                        )

            if first_name:
                _user.profile.telegram_first_name = first_name

            if last_name:
                _user.profile.telegram_last_name = last_name

            if last_name or first_name:
                _user.profile.save(update_fields=['telegram_first_name', 'telegram_last_name'])
