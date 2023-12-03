from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('AutoAnalizeFormula',)


class AutoAnalizeFormula(models.Model):
    code = models.CharField(max_length=6, unique=True, blank=False, null=False)
    comment = models.TextField(blank=False)
    attention_required = models.BooleanField(blank=True, default=False)

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['attention_required']),
        ]
        verbose_name = _('формула для автоанализа')
        verbose_name_plural = _('формулы для автоанализа')
