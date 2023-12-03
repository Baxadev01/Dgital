from datetime import date, timedelta

from django.utils import timezone

from content.models import TGChat
from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User

__all__ = ('MissedChannelLink', 'MissedChatLink',)


@sender.register
class MissedChannelLink(IMailing):
    SYSTEM_CODE = 'missed_channel_link'

    CRON_HOURS = 20
    CRON_MINUTES = 20

    def get_reference_date(self):
        # Each friday
        today = date.today()
        return today + timedelta((4 - today.weekday()) % 7)

    def get_users(self):
        now = timezone.now()
        last_day = now - timedelta(hours=72)
        chats_started_last_day = TGChat.objects.filter(
            start_date__gt=last_day, start_date__lte=now,
            is_active=True,
            is_main=True,
            is_moderated=True,
            chat_type='CHANNEL'
        )

        uq = User.objects

        uq = uq.filter(
            membership__chat__in=chats_started_last_day,
            membership__status='ALLOWED'
        ).distinct()

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

    def get_text_for_user(self, user):
        now = timezone.now()
        last_day = now - timedelta(hours=72)

        chats_started_last_day = TGChat.objects.filter(
            start_date__gt=last_day, start_date__lte=now,
            is_active=True,
            is_main=True,
            is_moderated=True,
            chat_type='CHANNEL'
        )

        chat = user.membership.filter(
            chat__in=chats_started_last_day,
            status='ALLOWED'
        ).first().chat
        message = self.template.replace('[JOINLINK]', 'https://t.me/joinchat/%s' % chat.tg_slug)
        return message


@sender.register
class MissedChatLink(IMailing):
    SYSTEM_CODE = 'missed_chat_link'

    CRON_HOURS = 20
    CRON_MINUTES = 20

    def get_reference_date(self):
        # Each friday
        today = date.today()
        return today + timedelta((4 - today.weekday()) % 7)

    def get_users(self):
        now = timezone.now()
        last_day = now - timedelta(hours=72)
        chats_started_last_day = TGChat.objects.filter(
            start_date__gt=last_day, start_date__lte=now,
            is_active=True,
            is_main=True,
            is_moderated=True,
            chat_type='CHAT'
        )

        uq = User.objects

        uq = uq.filter(
            membership__chat__in=chats_started_last_day,
            membership__status='ALLOWED'
        ).distinct()

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

    def get_text_for_user(self, user):
        now = timezone.now()
        last_day = now - timedelta(hours=72)

        chats_started_last_day = TGChat.objects.filter(
            start_date__gt=last_day, start_date__lte=now,
            is_active=True,
            is_main=True,
            is_moderated=True,
            chat_type='CHAT'
        )

        chat = user.membership.filter(
            chat__in=chats_started_last_day,
            status='ALLOWED'
        ).first().chat
        message = self.template.replace('[JOINLINK]', 'https://t.me/joinchat/%s' % chat.tg_slug)
        return message
