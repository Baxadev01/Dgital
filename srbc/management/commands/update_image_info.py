# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db.models.aggregates import Max
import datetime
from django.utils import dateformat
from srbc.models import User, Checkpoint, DiaryMeal, MealComponent, DiaryRecord
from srbc.utils.checkpoint_measurement import get_current_checkpoint_date, get_nearest_schedule_saturday

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ (DEV-300) Обновляет image_info коллажа днвника рациона."""
    help = "Updates diary.meal_image.image_info"

    def handle(self, *args, **options):
        statuses = ['PENDING', 'VALIDATION', 'FEEDBACK', 'DONE']
        qs = DiaryRecord.objects.filter(
            is_meal_validated=True, meal_status__in=statuses, meal_image__isnull=False, bed_time_is_next_day=True
        )
        for diary in qs.iterator():
            if diary.meal_image:
                text_date = diary.date - datetime.timedelta(days=1)
                text_date = dateformat.format(text_date, 'd E')

                wake_up_text = 'Подъём – %s' % diary.wake_up_time.strftime("%H:%M")
                meal_texts = []
                for meal in DiaryMeal.objects.filter(diary=diary).order_by('start_time_is_next_day', 'start_time'):
                    if meal.is_meal:
                        qs = MealComponent.objects.filter(meal=meal).only('description', 'weight')
                        components = ('%s %g' % (i.description, i.weight) for i in qs)
                        components_text = ', '.join(components)
                        dt = meal.start_time.strftime("%H:%M")
                        if meal.start_time_is_next_day:
                            dt = '%s (%s)' % (dt, diary.date.strftime("%Y-%m-%d"))
                        meal_texts.append('%s – %s' % (dt, components_text))

                    if meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
                        st_text = '%s' % meal.start_time.strftime("%H:%M")
                        et_text = '%s' % meal.end_time.strftime("%H:%M")

                        if meal.start_time_is_next_day:
                            st_text += ' (после полуночи)'
                        if meal.end_time_is_next_day:
                            et_text += ' (после полуночи)'

                        meal_texts.append('%s - %s – %s' % (st_text, et_text, 'Дневной сон'))

                    elif meal.meal_type == DiaryMeal.MEAL_TYPE_HUNGER:
                        dt = meal.start_time.strftime("%H:%M")
                        meal_texts.append('%s – %s. Интенсивность %s' % (dt, 'Чувство голода', meal.hunger_intensity))

                    elif meal.meal_type == DiaryMeal.MEAL_TYPE_BLOOD_GLUCOSE:
                        dt = meal.start_time.strftime("%H:%M")
                        meal_texts.append('%s – %s. %s %s' % (dt, 'Замер уровня глюкозы в крови',
                                                              meal.glucose_level, meal.glucose_unit))
                    else:
                        raise NotImplementedError

                meals_text = '\n'.join(meal_texts)

                dt = diary.bed_time.strftime("%H:%M")
                if diary.bed_time_is_next_day:
                    dt = '%s (%s)' % (dt, diary.date.strftime("%Y-%m-%d"))
                bed_time_text = 'Отбой – %s' % dt

                if diary.water_consumed:
                    water_text = 'Воды за день – %s л' % (round(diary.water_consumed * 10) / 10)
                else:
                    water_text = 'Воды за день – 0 л'

                hashtag_text = '#selfrebootcamp #selfrebootcampеда %s' % diary.meal_hashtag

                diary.meal_image.image_info = '\n'.join(
                    (text_date, wake_up_text, meals_text, bed_time_text, water_text, hashtag_text)
                )

                diary.meal_image.save(update_fields=['image_info'])
