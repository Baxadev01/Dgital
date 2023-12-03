# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from datetime import date
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import TGNotificationTemplate, TGNotification
from content.models.utils import generate_uuid
from crm.models import Campaign
from srbc.models import User, DiaryRecord, CheckpointPhotos, Tariff, Wave, TariffGroup

logger = logging.getLogger(__name__)

LAST_START = Wave.objects.filter(start_date__lte=date.today()).order_by('-start_date').first()
LAST_DATE = LAST_START.start_date + timedelta(days=2)
NOW = timezone.now() + timedelta(days=3)


def get_renewal_status(user):
    now = timezone.now() + timedelta(days=3)
    weeks_since_start = (now.date() - user.profile.wave.start_date).days / 7
    if weeks_since_start < 4:
        return None

    weeks_till_end = (user.profile.valid_until - now.date()).days / 7

    if weeks_till_end >= 4:
        return None

    weeks_to_check = 4 if weeks_since_start < 8 else 8

    if user.profile.tariff \
            and (
            user.profile.tariff.fee_rub == 0
            or (user.profile.tariff.tariff_next
                and user.profile.tariff.tariff_next.fee_rub == 0)):
        # print "NOT OK!"
        return None

    if user.profile.stat_group in ['EXCLUDE_REQUESTED']:
        return 'EXCLUDED'

    # Temporary allow everyone else to go on
    return 'OK'

    if weeks_to_check == 4:
        diaries_first_date = LAST_START.start_date - timedelta(days=25)
    else:
        diaries_first_date = LAST_START.start_date - timedelta(days=53)

    diaries_last_date = LAST_START.start_date + timedelta(days=2)

    diaries = DiaryRecord.objects.filter(user=user, date__gte=diaries_first_date, date__lte=diaries_last_date).all()

    meal_stat = {}
    weekends_total = weeks_to_check * 2
    days_total = weeks_to_check * 7
    weekends_meal = 0
    days_with_weight = 0
    days_with_steps = 0
    weeks_with_meals = 0

    if weeks_to_check == 4:
        checkpoints_first_date = LAST_START.start_date - timedelta(days=29)
        checkpoints_required = 3
    else:
        checkpoints_first_date = LAST_START.start_date - timedelta(days=44)
        checkpoints_required = 1 if user.profile.is_perfect_weight else 4

    checkpoints_last_date = LAST_START.start_date + timedelta(days=5)

    checkpoint_photos = CheckpointPhotos.objects.filter(
        user=user, date__gte=checkpoints_first_date, date__lte=checkpoints_last_date,
        status='APPROVED'
    ).order_by('date').all()

    checkpoint_photo_dates = [_c.date for _c in checkpoint_photos]

    checkpoint_photo_dates.sort()
    checkpoints_count = len(checkpoint_photo_dates)

    for _d in diaries:
        _date_shifted = _d.date + timedelta(days=3)
        _monday = _d.date - timedelta(days=_date_shifted.weekday())
        if _monday not in meal_stat:
            meal_stat[_monday] = 0

        if _d.meal_status == 'DONE':
            meal_stat[_monday] += 1
            if _d.date.weekday() in [5, 6]:
                weekends_meal += 1

        if _d.weight is not None:
            days_with_weight += 1

        if _d.steps is not None:
            days_with_steps += 1

    for _m, _c in list(meal_stat.items()):
        if _c >= 4:
            weeks_with_meals += 1

    if days_with_weight < Decimal(days_total) * Decimal(0.80):
        return 'WEIGHT'

    if days_with_steps < Decimal(days_total) * Decimal(0.66):
        return 'STEP'

    if checkpoints_count < checkpoints_required:
        return 'CHECKPOINT'

    if weeks_since_start < 20 and not user.profile.is_perfect_weight:
        if weeks_with_meals < Decimal(weeks_to_check) * Decimal(0.75):
            return 'MEALS'
        if weekends_meal < Decimal(weekends_total) * Decimal(0.75):
            return 'MEALS_WEEKEND'

    if user.profile.warning_flag in ['OOC', 'PR']:
        return 'ALARM'

    return 'OK'


class Command(BaseCommand):
    help = "Auto renew users"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        today = date.today()

        # проверяем, что старт был в течении недели
        min_start_day = today - timedelta(days=7)

        campaign_exist = Campaign.objects.filter(
            start_date__gte=min_start_day,
            start_date__lt=today
        ).exists()

        if not campaign_exist:
            return

        users = User.objects.filter(
            tariff_history__valid_from__lte=today,
            tariff_history__valid_until__gte=today,
            tariff_history__is_active=True,
            tariff_history__tariff__tariff_group__is_wave=True,
            tariff_history__tariff__tariff_group__communication_mode=TariffGroup.COMMUNICATION_MODE_CHANNEL
        )

        user_id = options.get('user', None)

        if user_id:
            users = users.filter(pk=user_id)
        else:
            users = users.filter(profile__tariff_next_id=None)

        users = users.all()

        tariff_channel = Tariff.objects.filter(slug='CHANNEL_RESUME').first()
        tariff_channel_club = Tariff.objects.filter(slug='CHANNEL_CLUB').first()
        tariff_channel_nodata = Tariff.objects.filter(slug='CHANNEL_NO_DATA').first()

        if not tariff_channel:
            raise Exception("Tariff Channel not found")

        if not tariff_channel_club:
            raise Exception("Tariff Channel Club not found")

        if not tariff_channel_nodata:
            raise Exception("Tariff Channel No-Data not found")

        tgm_fingerprint_prefix = 'renewal_%s_' % generate_uuid()
        stat = defaultdict(int)
        stat_details = defaultdict(list)
        for _u in users:
            renewal_status = get_renewal_status(user=_u)
            stat[renewal_status or 'none'] += 1
            stat_details[renewal_status or 'none'].append(_u.id)

            if renewal_status is None:
                continue
            print('%s %s' % (_u.id, renewal_status))
            # continue

            tgm_fingerprint = '%s%s' % (tgm_fingerprint_prefix, renewal_status.lower())
            tgm_template_code = 'renewal_notice_%s' % renewal_status.lower()

            tpl = TGNotificationTemplate.objects.get(system_code=tgm_template_code)

            TGNotification(
                user_id=_u.pk,
                content=tpl.text,
                fingerprint=tgm_fingerprint,
                status='PENDING'
            ).save()

            if renewal_status in ['EXCLUDED']:
                continue

            if _u.profile.active_tariff_history.tariff.tariff_next:
                _u.profile.tariff_next = _u.profile.active_tariff_history.tariff.tariff_next
            elif renewal_status in ['WEIGHT', 'STEP', 'CHECKPOINT']:
                _u.profile.tariff_next = tariff_channel_nodata
            elif _u.profile.is_in_club:
                _u.profile.tariff_next = tariff_channel_club
            else:
                _u.profile.tariff_next = tariff_channel

            _u.profile.save(update_fields=['tariff_next'])

            LogEntry.objects.log_action(
                user_id=settings.SYSTEM_USER_ID,
                content_type_id=ContentType.objects.get_for_model(_u.profile).pk,
                object_id=_u.profile.pk,
                object_repr=_u.username,
                action_flag=CHANGE,
                change_message="Auto-enabling renewal"
            )

        stat.pop('none', None)
        stat_details.pop('none', None)

        # stat.pop('OK', None)
        stat_details.pop('OK', None)

        print(stat)
        print(stat_details)
