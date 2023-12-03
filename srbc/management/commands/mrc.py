# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
from datetime import date
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from srbc.models import DiaryRecord, Wave
from srbc.utils.meal_recommenation import get_recommendation_fulfillment

logger = logging.getLogger(__name__)

LAST_START = Wave.objects.filter(start_date__lte=date.today()).order_by('-start_date').first()
LAST_DATE = LAST_START.start_date + timedelta(days=2)
NOW = timezone.now() + timedelta(days=3)


class Command(BaseCommand):
    help = "Check Meal for fitting Recommendations"

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, default=None)
        parser.add_argument('date', type=str, default=None)

    def handle(self, *args, **options):
        diary = DiaryRecord.objects.get(
            user_id=options.get('user_id'), date=options.get('date')
        )

        result = get_recommendation_fulfillment(diary)
        print(result)
