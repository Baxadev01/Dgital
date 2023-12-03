# -*- coding: utf-8 -*-
from decimal import Decimal
from datetime import timedelta

import logging

from django.db import transaction
from django.core.management.base import BaseCommand
from django.conf import settings

from srbc.models import User, Profile
from srbc.models import DiaryRecordCopy as DiaryRecord
# from srbc.models import DiaryRecord


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Extrapolate TrueWeight for user"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        user_id = options.get('user', None)

        users = User.objects

        if user_id:
            users = users.filter(pk=user_id)

        users = users.order_by('id').all()

        for _user in users:
            log_msg = 'Extrapolating TW for user user %s' % (_user.pk)
            print(log_msg)
            logger.info(log_msg)

            DiaryRecord.objects.filter(user=_user).update(trueweight=None)

            diaries = DiaryRecord.objects.filter(user=_user).exclude(weight__isnull=True).order_by('date').all()

            if not diaries:
                continue

            previous_day = None

            ma_coeff = Decimal(2 / (1 + float(settings.TRUEWEIGHT_DELAY)))

            for iter_diary in diaries:
                diary = DiaryRecord.objects.filter(date=iter_diary.date, user=iter_diary.user).first()
                if not diary:
                    continue

                if previous_day is None:
                    if diary.trueweight is None:
                        diary.trueweight = diary.weight
                        diary.save()

                else:

                    days_diff = (diary.date - previous_day.date).days
                    power = Decimal(min(1, ma_coeff * days_diff))

                    diary.trueweight = power * diary.weight + (1 - power) * previous_day.trueweight
                    diary.save()

                    if days_diff > 1:
                        print('Filling linear trueweight between %s [%.2f] and %s [%.2f]' % (
                            previous_day.date,
                            previous_day.trueweight,
                            diary.date,
                            diary.trueweight,
                        ))

                        tw_delta_per_day = (diary.trueweight - previous_day.trueweight) / Decimal(days_diff)

                        # если пропущены записи в дневнике, то забиваем пропуски записями,
                        # и ставим вес равный последнему до пропуска
                        # сделаем блокировку сразу, до цикла, чтобы не делать в каждой итерации

                        with transaction.atomic():
                            # Locking
                            Profile.objects.select_for_update().get(user=_user)

                            for i in range(1, days_diff):
                                _diary_date = previous_day.date + timedelta(days=i)
                                _diary = DiaryRecord.objects.filter(user=_user, date=_diary_date).first()
                                if not _diary:
                                    _diary = DiaryRecord(user=_user, date=_diary_date)

                                _diary.trueweight = previous_day.trueweight + tw_delta_per_day * i
                                print('Filling trueweight for %s: %.2f' % (_diary.date, _diary.trueweight))

                                _diary.save()

                previous_day = diary
