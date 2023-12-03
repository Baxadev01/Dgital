from django.db import models

from .diary_meal import DiaryMeal
from .diary_record import DiaryRecord
from .meal_component import MealComponent
from .meal_fault import MealFault

__all__ = ('DiaryMealFault',)


class DiaryMealFault(models.Model):
    fault = models.ForeignKey(MealFault, on_delete=models.CASCADE)
    diary_record = models.ForeignKey(DiaryRecord, related_name="faults_list", on_delete=models.CASCADE)
    meal = models.ForeignKey(DiaryMeal, blank=True, null=True, on_delete=models.SET_NULL)
    meal_component = models.ForeignKey(MealComponent, blank=True, null=True, on_delete=models.SET_NULL)
    comment = models.TextField(blank=True, null=True)
