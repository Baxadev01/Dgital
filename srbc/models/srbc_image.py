import os

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from markdownx.models import MarkdownxField

__all__ = ('SRBCImage', 'srbc_image_upload_to',)


def srbc_image_upload_to(instance, filename):
    return os.path.join(
        'srbc-images',
        "%s" % instance.user_id,
        "%s" % instance.date.strftime('%Y-%m-%d'),
        "%s" % instance.image_type,
        filename
    )


class SRBCImage(models.Model):
    user = models.ForeignKey(User, related_name="photo_stream", on_delete=models.CASCADE)
    date = models.DateField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    image_info = MarkdownxField(default=None, null=True, blank=True)
    image_type = models.CharField(
        max_length=100,
        choices=(
            ('MEAL', 'Рацион'),
            ('DATA', 'Данные'),
            ('CHECKPOINT_PHOTO', 'Контрольные фото'),
            ('CHECKPOINT_PHOTO_FRONT', 'Сравнительные фото - анфас'),
            ('CHECKPOINT_PHOTO_SIDE', 'Сравнительные фото - сбоку'),
            ('CHECKPOINT_PHOTO_REAR', 'Сравнительные фото - сзади'),
            ('CHECKPOINT_MEASUREMENTS', 'Контрольные замеры'),
            ('CHECKPOINT_CHARTS', 'Контрольный TrueWeight'),
            ('MEDICAL', 'Результаты медицинских обследований'),
            ('GOALS', 'Цели (написанные от руки и сфотографированные)'),
            ('OTHER', 'Другое'),
        )
    )
    # 600х600
    thumbnail = models.ImageField(
        blank=True, null=True, upload_to=srbc_image_upload_to
    )
    # 1200х1200
    image = models.ImageField(
        blank=True, null=True, upload_to=srbc_image_upload_to
    )
    is_editable = models.BooleanField(blank=True, default=True)
    is_published = models.BooleanField(blank=True, default=True)
    meta_data = models.JSONField(blank=True, default=dict)

    @property
    def custom_image_is_editable(self):
        """ Изменять текст кастомной картиники можно в течение часа после загрузки.

        :rtype: bool
        """
        return self.is_editable and \
               ((timezone.now() - self.date_added).seconds < 3600) and \
               (self.image_type in ('MEDICAL', 'GOALS', 'OTHER'))

    class Meta:
        verbose_name = _('Фото-лента')
        verbose_name_plural = _('Фото-лента')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
            models.Index(fields=['image_type']),
            models.Index(fields=['is_published']),
        ]
