from django.db import models
from django.utils.translation import ugettext_lazy as _

from markdownx.models import MarkdownxField

__all__ = ('TelegramMailTemplate',)


class TelegramMailTemplate(models.Model):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True, unique=True)
    text = MarkdownxField(blank=True, default='', null=True)
