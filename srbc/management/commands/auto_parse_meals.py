# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from srbc.models import ProfileTwoWeekStat, DiaryRecord
from srbc.utils.diary import diary_meal_pre_analyse, diary_meal_analyse
from srbc.utils.meal_parsing import get_meal_faults

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Proccess all pending meals "

    def handle(self, *args, **options):
        diaries = DiaryRecord.objects.filter(
            meal_status='PENDING', date__lte=timezone.now().date() - timedelta(days=7)
        ).all()
        for diary in diaries:
            print('User: %s, %s' % (diary.user_id, diary.date))
            diary_meal_pre_analyse(diary)

            faults_list, error = get_meal_faults(diary)

            if error:
                diary.is_fake_meals = True
                diary.meal_status = 'FAKE'
                diary.is_meal_reviewed = True
                diary.save(update_fields=['meal_status', 'is_meal_reviewed', 'is_fake_meals'])
            else:
                faults_count = 0
                for _f in faults_list:
                    _f.save()
                    if _f.fault.is_public:
                        faults_count += 1

                diary.faults = faults_count
                diary.meal_status = 'DONE'
                diary.is_meal_reviewed = True
                diary.save(update_fields=['faults', 'meal_status', 'is_meal_reviewed'])

            diary.save()
