from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('TGTranslation',)


class TGTranslation(models.Model):
    key = models.CharField(max_length=100, blank=False, null=False, unique=True)
    translation = models.TextField(blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _(u'перевод фразы TG-бота')
        verbose_name_plural = _(u'переводы фразы TG-бота')
