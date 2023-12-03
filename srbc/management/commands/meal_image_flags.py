# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from srbc.models import User, MealComponent, DiaryRecord, DiaryMeal, SRBCImage
from datetime import date
import requests
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update flags on meal images"

    def handle(self, *args, **options):
        alco = MealComponent.objects.filter(component_type='alco', meal__diary__meal_image__isnull=False).all()
        for component in alco:
            component.meal.diary.meal_image.meta_data['has_alco'] = True
            component.meal.diary.meal_image.save(update_fields=['meta_data'])

        sugar = MealComponent.objects.filter(component_type='desert', meal__diary__meal_image__isnull=False).all()
        for component in sugar:
            component.meal.diary.meal_image.meta_data['has_sugar'] = True
            component.meal.diary.meal_image.save(update_fields=['meta_data'])
