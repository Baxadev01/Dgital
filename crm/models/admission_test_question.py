from django.db import models
from django.utils.translation import ugettext_lazy as _

from markdownx.models import MarkdownxField

__all__ = ('AdmissionTestQuestion',)


class AdmissionTestQuestion(models.Model):
    text = MarkdownxField(blank=False)
    is_active = models.BooleanField(blank=True, default=False)
    answer_ok = models.BooleanField(blank=True, default=False, verbose_name="Соответствует методичке")
    answer_sweet = models.BooleanField(blank=True, default=False, verbose_name="Сладкое натощак")
    answer_interval = models.BooleanField(blank=True, default=False, verbose_name="Нарушены интервалы")
    answer_protein = models.BooleanField(blank=True, default=False, verbose_name="Недостаток белка")
    answer_carb = models.BooleanField(blank=True, default=False, verbose_name="Неверное количество углеводов")
    answer_fat = models.BooleanField(blank=True, default=False, verbose_name="Превышение жирности")
    answer_weight = models.BooleanField(blank=True, default=False, verbose_name="Неверные навески")

    def __str__(self):
        return '%s #%s' % (self.__class__.__name__, self.pk)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.pk)

    class Meta:
        pass
