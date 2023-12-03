from django.db import models
from django.utils.translation import ugettext_lazy as _

from markdownx.models import MarkdownxField

from .admission_test_question import AdmissionTestQuestion
from .user_admission_test import UserAdmissionTest

__all__ = ('UserAdmissionTestQuestion',)


class UserAdmissionTestQuestion(models.Model):
    source_question = models.ForeignKey(AdmissionTestQuestion, related_name="question_usage", on_delete=models.CASCADE)
    admission_test = models.ForeignKey(UserAdmissionTest, related_name="questions", on_delete=models.CASCADE)
    question_num = models.SmallIntegerField()
    is_answered = models.BooleanField(blank=True, default=False)
    text = MarkdownxField(blank=False)

    answer_ok = models.BooleanField(blank=True, default=False, verbose_name="Соответствует методичке")
    answer_ok_comment = models.TextField(blank=True, null=True)
    answer_sweet = models.BooleanField(blank=True, default=False, verbose_name="Сладкое натощак")
    answer_sweet_comment = models.TextField(blank=True, null=True)
    answer_interval = models.BooleanField(blank=True, default=False, verbose_name="Нарушены интервалы")
    answer_interval_comment = models.TextField(blank=True, null=True)
    answer_protein = models.BooleanField(blank=True, default=False, verbose_name="Недостаток белка")
    answer_protein_comment = models.TextField(blank=True, null=True)
    answer_carb = models.BooleanField(blank=True, default=False, verbose_name="Неверное количество углеводов")
    answer_carb_comment = models.TextField(blank=True, null=True)
    answer_fat = models.BooleanField(blank=True, default=False, verbose_name="Превышение жирности")
    answer_fat_comment = models.TextField(blank=True, null=True)
    answer_weight = models.BooleanField(blank=True, default=False, verbose_name="Неверные навески")
    answer_weight_comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['admission_test', 'question_num']
        indexes = [
            models.Index(fields=['is_answered']),
            models.Index(fields=['admission_test']),
            models.Index(fields=['source_question']),
        ]
