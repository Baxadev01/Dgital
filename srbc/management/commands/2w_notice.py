# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_telegrambot.apps import DjangoTelegramBot

from srbc.models import User, UserNote, TariffGroup
from srbc.views.api.v1.analytics import result_notice_gen

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generates Stat Notices for active users"

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()

        periods_passed = (today - settings.ANALYSIS_DATA_START_DATE).days // 14
        last_period_start = settings.ODD_WEEK_START_DATE + timedelta(days=14 * periods_passed)
        last_period_end = last_period_start + timedelta(days=13)

        mode_to_notice = [
            TariffGroup.DIARY_ANALYZE_MANUAL, 
            TariffGroup.DIARY_ANALYZE_AUTO,
            TariffGroup.DIARY_ANALYZE_BY_REQUEST
        ]

        stat_users = User.objects.filter(
            tariff_history__is_active=True,
            tariff_history__valid_from__lte=today,
            tariff_history__valid_until__gte=today,
            tariff_history__tariff__tariff_group__diary_analyze_mode__in=mode_to_notice,
            # tariff_history__tariff__tariff_group__is_wave=True,
            tariff_history__wave__start_date__lte=last_period_start
        )
        stat_users = stat_users.all()

        notices_created = 0

        for user in stat_users:
            notice_exists = UserNote.objects.filter(
                user=user, label=UserNote.LABEL_STAT,
                date_added__gte=last_period_end
            ).exists()

            if notice_exists:
                continue

            notices_created += 1
            new_notice = UserNote()
            new_notice.label = 'STAT'
            new_notice.user = user
            new_notice.date_added = now
            new_notice.author_id = settings.SYSTEM_USER_ID
            new_notice.is_published = True
            new_notice.content = result_notice_gen(user)
            new_notice.save()

        info_msg = 'Stat report generated for %s users.' % notices_created

        DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=settings.CHATBOT_NOTIFICATION_GROUP_ID,
            text=info_msg,
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )
