
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .utils import generate_uuid, picture_upload_to

__all__ = ('Picture',)


class Picture(models.Model):
    title = models.CharField(max_length=255)
    uid = models.CharField(max_length=32, blank=True, default=generate_uuid)
    image = models.ImageField(upload_to=picture_upload_to, null=True, blank=True)

    class Meta:
        verbose_name = _('изображение')
        verbose_name_plural = _('изображения')
