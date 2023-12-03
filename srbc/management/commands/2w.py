# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from srbc.models import ProfileTwoWeekStat

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fills statistics for regular analyse (srbc.ProfileTwoWeekStat)"

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()

        periods_passed = (today - settings.ANALYSIS_DATA_START_DATE).days // 14
        last_period_start = settings.ODD_WEEK_START_DATE + timedelta(days=14 * periods_passed)
        last_period_end = last_period_start + timedelta(days=13)

        if ProfileTwoWeekStat.objects.filter(date=last_period_end).exists():
            logger.info(
                'Statistics for this period (%s - %s) already exists.' % (
                    last_period_start, last_period_end,
                )
            )
            return None

        call_command('2w_stat')

        call_command('2w_notice')

        call_command('2w_analyze')

