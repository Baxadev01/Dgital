from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('Basics',)


class Basics(models.Model):
    keyword = models.CharField(max_length=100)
    body = models.TextField()
    type = models.CharField(max_length=20, choices=(
        ("TEXT", "Текст"),
        ("IMAGE", "Изображение"),
    ), default="TEXT")

    class Meta:
        indexes = [
            models.Index(fields=['keyword', 'type']),
        ]

        verbose_name = _('азы')
        verbose_name_plural = _('азы')
