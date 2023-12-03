import os

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('InstagramImage', 'ig_upload_to',)


def ig_upload_to(instance, filename):
    return os.path.join('ig', "%s" % instance.user_id, "%s" % instance.image_id, filename)


class InstagramImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_date = models.DateTimeField()
    loaded_date = models.DateTimeField()
    real_date = models.DateField(blank=True, null=True)
    # instagram_account = models.ForeignKey(UserSocialAuth)
    image_id = models.CharField(max_length=255)
    post_url = models.CharField(max_length=1024)
    default_image_url = models.CharField(max_length=1024, blank=True)
    image_urls = models.JSONField(blank=True, default=dict)
    image = models.ImageField(blank=True, null=True, upload_to=ig_upload_to, max_length=1024)
    post_text = models.TextField(blank=True, null=True)
    tags = ArrayField(models.CharField(max_length=100))
    role = models.CharField(
        max_length=100,
        choices=(
            ('FOOD', _("ЕДА")),
            ('PHOTO', _("ФОТО")),
            ('DATA', _("ДАННЫЕ")),
            ('MEASURE', _("ЗАМЕРЫ")),
            ('UNKNOWN', _("N/A")),
            ('GOAL', _("ЦЕЛИ"))
        )
    )
    is_deleted = models.BooleanField(blank=True, default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['post_date']),
            models.Index(fields=['role']),
            models.Index(fields=['image_id']),
            models.Index(fields=['tags']),
        ]
