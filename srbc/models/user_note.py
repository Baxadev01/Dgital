from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from markdownx.models import MarkdownxField

from shared.models import IntegerRangeField

__all__ = ('UserNote', 'default_policy',)


def default_policy():
    return settings.SYSTEM_USER_ID


class UserNote(models.Model):
    """ Рекомендации """
    LABEL_DOC = 'DOC'
    LABEL_PZDC = 'PZDC'
    LABEL_WTF = 'WTF'
    LABEL_IG = 'IG'
    LABEL_CHAT = 'CHAT'
    LABEL_NB = 'NB'
    LABEL_ORG = 'ORG'
    LABEL_STAT = 'STAT'

    user = models.ForeignKey(
        User, related_name='notes', limit_choices_to={'groups__name': "Participant"}, on_delete=models.CASCADE
    )
    author = models.ForeignKey(User, related_name='notes_by', on_delete=models.SET_DEFAULT, default=default_policy,
                               limit_choices_to={'groups__name__in': ["Doc", "TeamLead", "UserNotes Manager"]})
    label = models.CharField(
        max_length=100,
        choices=(
            (LABEL_DOC, _("Док / Обследования")),
            (LABEL_PZDC, _("Кризис")),
            (LABEL_WTF, _("Протокол участия")),
            (LABEL_IG, _("Регулярный анализ")),
            (LABEL_CHAT, _("Корректировка рациона")),
            (LABEL_NB, _("Служебная заметка")),
            (LABEL_ORG, _("Организационные вопросы")),
            (LABEL_STAT, _("Статистический отчёт")),
        )
    )
    content = MarkdownxField(blank=True, default='')
    date_added = models.DateTimeField(default=timezone.now, blank=True)
    is_published = models.BooleanField(blank=True, default=False, verbose_name="Видно участнику")
    is_notification_sent = models.BooleanField(blank=True, default=False, verbose_name="Уведомлён")

    # параметризация рекомендаций
    adjust_calories = IntegerRangeField(blank=True, min_value=-100, max_value=100, default=0)  # калорийность рациона
    adjust_protein = IntegerRangeField(blank=True, min_value=0, max_value=100, default=0)  # белок
    add_fat = models.BooleanField(blank=True, default=False)  # добавить жиров
    adjust_fruits = models.CharField(  # ограничение фруктов
        choices=(
            ('NO', 'Без дополнительных ограничений'),
            ('RESTRICT', 'Минимизация моно- и дисахаридов'),
            ('EXCLUDE', 'Замена моно- и дисахаридов'),
        ),
        blank=True,
        max_length=20,
        default='NO'
    )
    adjust_carb_mix_vegs = models.BooleanField(blank=True, default=False)  # смешивание овощей

    adjust_carb_bread_min = models.BooleanField(blank=True,
                                                default=False)  # ограничение углеводов - минимизировать хлеб
    adjust_carb_bread_late = models.BooleanField(blank=True,
                                                 default=False)  # ограничение углеводов - убрать хлеб из ужина
    # ограничение углеводов - исключить запасающие овощи после обеда
    adjust_carb_carb_vegs = models.BooleanField(blank=True, default=False)
    adjust_carb_sub_breakfast = models.BooleanField(blank=True, default=False)  # замена длинных углеводов
    exclude_lactose = models.BooleanField(blank=True, default=False)
    restrict_lactose_casein = models.BooleanField(blank=True, default=False)

    @property
    def has_meal_adjustments(self):
        return any([
            self.adjust_calories, self.adjust_protein,
            self.add_fat,
            self.adjust_carb_bread_min, self.adjust_carb_bread_late,
            self.adjust_carb_carb_vegs, self.adjust_carb_sub_breakfast,
            self.exclude_lactose, self.restrict_lactose_casein,
            self.adjust_carb_mix_vegs,
            self.adjust_fruits != 'NO',
        ])

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['label']),
            models.Index(fields=['date_added']),
            models.Index(fields=['is_published']),
        ]

        verbose_name = _('заметка участника')
        verbose_name_plural = _('заметки участников')
