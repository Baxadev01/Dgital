# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from srbc.models import User, DiaryRecord, StatGroupHistory, UserNote, Profile
from datetime import date, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def set_user_meal_mode(user, mode):
    user.profile.meal_analyze_mode = mode
    user.profile.save(update_fields=['meal_analyze_mode'])


class Command(BaseCommand):
    help = "Setting Meal Analyze Mode for users"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        user_id = options.get('user', None)

        now = timezone.now()

        users = User.objects.filter(
            is_staff=False,
            tariff_history__valid_until__gte=now.date(),
            tariff_history__valid_from__lte=now.date(),
            tariff_history__is_active=True,
            tariff_history__tariff__tariff_group__is_wave=True
        ).select_related('profile').order_by('tariff_history__wave_id')

        if user_id:
            users = users.filter(pk=user_id)

        users = users.all()
        modes_count = {
            Profile.MEAL_ANALYZE_MODE_FULL_TEXT: 0,
            Profile.MEAL_ANALYZE_MODE_SHORT_TEXT: 0,
            Profile.MEAL_ANALYZE_MODE_NO_TEXT: 0,
            Profile.MEAL_ANALYZE_MODE_AUTO: 0,
        }

        for _u in users:
            weeks_since_start = (now.date() - _u.profile.wave.start_date).days / 7

            if _u.profile.is_meal_analyze_mode_locked:
                modes_count[_u.profile.meal_analyze_mode] += 1
            else:
                if weeks_since_start < 4:
                    mode_to_set = Profile.MEAL_ANALYZE_MODE_FULL_TEXT
                elif weeks_since_start < 12:
                    mode_to_set = Profile.MEAL_ANALYZE_MODE_SHORT_TEXT
                elif weeks_since_start < 20:
                    mode_to_set = Profile.MEAL_ANALYZE_MODE_NO_TEXT
                else:
                    mode_to_set = Profile.MEAL_ANALYZE_MODE_AUTO

                set_user_meal_mode(user=_u, mode=mode_to_set)
                modes_count[mode_to_set] += 1

        print(modes_count)
