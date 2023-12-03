from django.db import models
from django.utils.translation import ugettext_lazy as _

from markdownx.models import MarkdownxField

__all__ = ('AnalysisTemplate',)


class AnalysisTemplate(models.Model):
    """ Шаблон рекомендаций """
    title = models.CharField(max_length=255)
    text = MarkdownxField(verbose_name='Текст анализа')
    is_visible = models.BooleanField(blank=True, default=True)
    display_mode = models.CharField(
        max_length=50,
        choices=(
            ('default', 'Default'),
            ('success', 'Success'),
            ('info', 'Info'),
            ('primary', 'Primary'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
        ),
        default='default'
    )
    order_num = models.IntegerField(blank=True, default=99)

    # параметризация рекомендаций
    # корректировка калорийности рациона
    adjust_calories = models.BooleanField(default=False, verbose_name='Корректировка калорийности рациона')
    # корректировка белка в рационе
    adjust_protein = models.BooleanField(
        default=False, verbose_name='Корректировка белка в рационе')
    # Добавить жиров
    add_fat = models.BooleanField(null=True, verbose_name='Добавить жиров')
    # ограничение фруктов
    adjust_fruits = models.CharField(
        choices=(
            ('NO', 'без дополнительных ограничений'),
            ('RESTRICT', 'ограничение фруктов'),
            ('EXCLUDE', 'замена фруктов'),
        ),
        blank=True,
        max_length=20,
        null=True,
        verbose_name='Ограничение фруктов'
    )

    # смешивание овощей
    adjust_carb_mix_vegs = models.BooleanField(null=True, verbose_name='Смешивать овощи')
    # ограничение углеводов - минимизировать хлеб
    adjust_carb_bread_min = models.BooleanField(null=True, verbose_name='Минимизировать хлеб')
    # ограничение углеводов - убрать хлеб из ужина
    adjust_carb_bread_late = models.BooleanField(null=True, verbose_name='Убрать хлеб из ужина')
    # ограничение углеводов - исключить запасающие овощи после обеда
    adjust_carb_carb_vegs = models.BooleanField(null=True, verbose_name='Исключить запасающие овощи после обеда')
    # замена длинных углеводов
    adjust_carb_sub_breakfast = models.BooleanField(null=True, 
        verbose_name='Замена длинных углеводов на овощи(завтрак посхеме обеда)')

    system_code = models.CharField(max_length=255, unique=True, blank=True, default=None, null=True)

    class Meta:
        ordering = ['order_num']
        indexes = [
            models.Index(fields=['is_visible']),
            models.Index(fields=['order_num']),
            models.Index(fields=['system_code']),
        ]
        verbose_name = _('шаблон анализа')
        verbose_name_plural = _('шаблоны анализа')
