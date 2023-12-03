# -*- coding: utf-8 -*-
import logging
import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_telegrambot.apps import DjangoTelegramBot
from lockfile import locked

from content.tgmails import sender as tgm_sender
from content.utils import store_dialogue_reply

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sending SendMail to TG"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    @locked('/tmp/srbc_content_tg_sendmail.lock', 0)
    def handle(self, *args, **options):
        user_id = options.get('user', None)

        notes_qs = tgm_sender.get_tg_mails_to_send()
        if user_id:
            notes_qs = notes_qs.filter(user_id=user_id)

        for _note in notes_qs:
            _note.last_attempt_at = timezone.now()

            if not _note.user.profile.telegram_id:
                _note.status = 'ERROR'
                _note.error_message = 'User does not have Telegram ID'
                _note.save()
                continue

            try:
                msg = DjangoTelegramBot.dispatcher.bot.send_message(
                    chat_id=_note.user.profile.telegram_id,
                    text=_note.content,
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                    timeout=5
                )
            except Exception as e:
                _note.status = 'ERROR'
                _note.error_message = e.message if hasattr(e, 'message') else str(e)
                _note.save()
                continue

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
            _note.status = 'SENT'
            _note.sent_at = timezone.now()
            _note.save()
            time.sleep(2)
