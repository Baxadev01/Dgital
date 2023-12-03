# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from srbc.models import User, DiaryRecord, StatGroupHistory, UserNote
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Setting Stat Group for users"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        user_id = options.get('user', None)
        today = date.today()
        users = User.objects.filter(
            is_staff=False,
            tariff_history__valid_until__gte=today,
            tariff_history__valid_from__lte=today,
            tariff_history__is_active=True,
            tariff_history__tariff__tariff_group__is_wave=True,
            tariff_history__tariff__tariff_group__is_in_club=False
        ).select_related('profile')

        if user_id:
            users = users.filter(pk=user_id)

        users = users.all()

        for _user in users:
            if _user.profile.stat_group in ['EXCLUDE_REQUESTED', ]:
                continue

            if _user.profile.stat_group in ['EXCLUDE_REQUESTED_TMP']:
                if not _user.profile.away_until:
                    continue

                if _user.profile.away_until <= date.today():
                    _user.profile.stat_group = 'EXCLUDE_FORCED_REANIMATED'
                    _user.profile.save(update_fields=['stat_group'])
                    continue

            log_msg = 'Analizing user %s (#%s)' % (_user.username, _user.pk)
            print(log_msg)
            logger.info(log_msg)

            days_since_start = (date.today() - _user.profile.wave.start_date).days

            if days_since_start < 14:
                print("less than 2 weeks from start")
                _user.profile.stat_group = 'INCLUDE_GENERAL'
                _user.profile.save(update_fields=['stat_group'])
                continue

            interval_start = date.today() - timedelta(days=date.today().weekday(), weeks=2)
            interval_end = interval_start + timedelta(days=13)

            print("Dates: %s - %s" % (interval_start, interval_end))

            days_in_dates = DiaryRecord.objects.filter(
                user=_user,
                date__gte=interval_start, date__lte=interval_end,
                meal_status__in=['PENDING', 'DONE'],
                is_fake_meals=False,
                weight__isnull=False,
                steps__isnull=False
            ).count()

            if days_in_dates >= 7:
                days_with_faults = DiaryRecord.objects.filter(
                    user=_user,
                    date__gte=interval_start, date__lte=interval_end,
                    meal_status__in=['PENDING', 'DONE'],
                    is_fake_meals=False,
                    weight__isnull=False,
                    steps__isnull=False,
                    faults__gt=0
                ).count()

                if (1.0 * days_with_faults) / days_in_dates >= 0.5:
                    print("days with faults %s of %s" % (days_with_faults, days_in_dates))

                    _user.profile.stat_group = 'INCLUDE_BASELINE'
                else:
                    if _user.profile.warning_flag in ['PR']:
                        print("Purple flag")
                        _user.profile.stat_group = 'INCLUDE_GENERAL'
                    else:
                        personal_recommendations = UserNote.objects.filter(
                            date_added__gte=_user.profile.wave.start_date,
                            label__in=['IG'],
                            is_published=True
                        ).exists()

                        if personal_recommendations:
                            print("OK")
                            _user.profile.stat_group = 'INCLUDE_MAIN'
                        else:
                            print("No personal recomendations")
                            _user.profile.stat_group = 'INCLUDE_GENERAL'

            else:
                if _user.profile.stat_group == 'EXCLUDE_FORCED_REANIMATED':
                    last_stat_group_change = StatGroupHistory.objects.filter(user=_user).order_by('-id').first()

                    if not last_stat_group_change:
                        continue

                    if not last_stat_group_change.active_from:
                        continue

                    if (interval_end - last_stat_group_change.active_from).days < 7:
                        continue

                    interval_start_week = date.today() - timedelta(days=date.today().weekday(), weeks=1)

                    days_in_dates_week = DiaryRecord.objects.filter(
                        user=_user,
                        date__gte=interval_start_week, date__lte=interval_end,
                        meal_status__in=['PENDING', 'DONE'],
                        is_fake_meals=False,
                        weight__isnull=False,
                        steps__isnull=False
                    ).count()

                    if days_in_dates_week < 5:
                        print("After Reanimation only %s days with data since last week" % days_in_dates_week)
                        _user.profile.stat_group = 'EXCLUDE_FORCED'

                else:
                    print("Days with data for last two weeks: %s" % days_in_dates)
                    _user.profile.stat_group = 'EXCLUDE_FORCED'

            _user.profile.save(update_fields=['stat_group'])
