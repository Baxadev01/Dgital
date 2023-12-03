from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('TGNotificationTemplate',)


class TGNotificationTemplate(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    is_visible = models.BooleanField(blank=True, default=True)
    display_mode = models.CharField(
        max_length=50,
        choices=(
            ('default', 'Default'),
            ('success', 'Success'),
            ('info', 'Info'),
            ('primary', 'Primary'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
        ),
        default='default'
    )
    system_code = models.CharField(blank=True, null=True, max_length=32, unique=True)
    order_num = models.IntegerField(blank=True, default=99)

    class Meta:
        ordering = ['order_num']
