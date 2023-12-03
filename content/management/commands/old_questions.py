# -*- coding: utf-8 -*-
import logging
import time
from django.conf import settings
from django_telegrambot.apps import DjangoTelegramBot
from django.core.management.base import BaseCommand
from content.models import TGMessage
from django.utils import timezone
from datetime import timedelta
from srbc.utils.helpers import pluralize

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ Отслыает уведомления о неотвеченных вопросах и отзывах"""
    help = "Meetings converting"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        now = timezone.now()
        pending_messages = TGMessage.objects \
            .filter(status='NEW', created_at__lte=now - timedelta(hours=12)) \
            .select_related('author', 'author__profile').order_by('created_at').all()
        report_message_template = "`#%(i)s`: *%(message_type)s* " \
                                  "от участника *%(uname)s* (id:[%(uid)s](https://lk.selfreboot.camp/profile/!%(uid)s/)) " \
                                  "ожидает ответа уже %(hours)s %(hours_title)s.\n\n" \
                                  "```\n%(message_text)s\n```"

        if not pending_messages:
            logger.info("No old messages in channel")
            return

        attempts = 1
        is_sent = False
        messages_count = len(pending_messages)
        messages_count_title = pluralize(messages_count, ["сообщение", "сообщения", "собщений"])
        messages_sent_title = pluralize(messages_count, ["отправленное", "отправленных", "отправленных"])
        while (not is_sent) and (attempts < 3):
            try:
                DjangoTelegramBot.dispatcher.bot.send_message(
                    chat_id=settings.CHATBOT_STAFF_GROUP_ID,
                    text="⏰❗⏰❗⏰❗⏰❗⏰❗⏰❗⏰❗⏰❗⏰\n\nОбнаружено %s %s, %s более 12 часов назад:" % (
                        messages_count,
                        messages_count_title,
                        messages_sent_title,
                    ),
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                    timeout=5
                )
                is_sent = True
            except Exception:
                attempts += 1
        i = 0
        for message in pending_messages:
            i += 1
            hours_passed = int((now - message.created_at).total_seconds() / 3600)
            message_type = message.get_message_type_display()
            hours_title = pluralize(hours_passed, ["час", "часа", "часов"])
            report_message = report_message_template % {
                "i": i,
                "message_type": message_type,
                "uname": message.author.username,
                "uid": message.author_id,
                "hours": hours_passed,
                "hours_title": hours_title,
                "message_text": message.text,
            }

            attempts = 1
            is_sent = False
            while (not is_sent) and (attempts < 3):
                try:
                    DjangoTelegramBot.dispatcher.bot.send_message(
                        chat_id=settings.CHATBOT_STAFF_GROUP_ID,
                        text=report_message,
                        disable_web_page_preview=True,
                        parse_mode='Markdown',
                        timeout=5
                    )
                    is_sent = True
                    time.sleep(1)
                except Exception as e:
                    attempts += 1
                    if attempts >= 3:
                        # print 'Failed to send message: ' + str(e) + "\n"
                        logger.error('Failed to send message: ' + str(e))
