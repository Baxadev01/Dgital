from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('Recipe',)


class Recipe(models.Model):
    title = models.CharField(max_length=225)
    body = models.TextField()
    comment = models.TextField(default='', blank=True)
    tags = ArrayField(models.CharField(max_length=100))

    def __str__(self):
        return self.title

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.pk)

    class Meta:
        verbose_name = _('рецепт')
        verbose_name_plural = _('рецепты')
