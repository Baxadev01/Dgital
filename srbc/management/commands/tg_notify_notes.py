# -*- coding: utf-8 -*-
import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_telegrambot.apps import DjangoTelegramBot
from lockfile import locked

from content.utils import store_dialogue_reply
from content.models import TGNotificationTemplate
from srbc.models import UserNote

from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sending UserNote Notifications"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    @locked('/tmp/srbc_tg_usernotes_notify.lock', 0)
    def handle(self, *args, **options):
        user_id = options.get('user', None)

        notes = UserNote.objects.filter(
            is_published=True, date_added__lte=timezone.now(), is_notification_sent=False,
            date_added__gte=timezone.now() - timedelta(hours=12)
        ).exclude(
            label__in=['DOC']
        ).order_by('date_added')

        if user_id:
            notes = notes.filter(user_id=user_id)

        for _note in notes:
            if not _note.user.profile.telegram_id:
                continue
            
            try:
                code = 'usernote_notification_%s' % _note.label
                tpl = TGNotificationTemplate.objects.get(system_code=code)

                post_notification = tpl.text.replace('USER_NOTE', "\n\n```\n%s\n```\n" % _note.content)

                msg = DjangoTelegramBot.dispatcher.bot.send_message(
                    chat_id=_note.user.profile.telegram_id,
                    text=post_notification,
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                    timeout=5
                )
            except TGNotificationTemplate.DoesNotExist:
                logger.error('tg_notify_notes. Template not found %s', code)
                capture_exception(Exception('tg_notify_notes. Template not found %s', code))
                continue

            except Exception as e :
                continue

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
            _note.is_notification_sent = True
            _note.save(update_fields=['is_notification_sent'])
            time.sleep(1)
