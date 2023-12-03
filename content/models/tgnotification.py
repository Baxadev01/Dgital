from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .tgmessage import TGMessage

__all__ = ('TGNotification',)


class TGNotification(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_SENT = 'SENT'
    STATUS_ERROR = 'ERROR'

    STATUS_ITEM = (
        (STATUS_PENDING, _("Pending")),
        (STATUS_SENT, _("Sent")),
        (STATUS_ERROR, _("Error")),
    )

    user = models.ForeignKey(User, related_name='tg_notifications', on_delete=models.CASCADE)
    content = models.TextField()
    fingerprint = models.CharField(max_length=64)
    status = models.CharField(
        choices=STATUS_ITEM,
        default=STATUS_PENDING,
        max_length=64
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_attempt_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True, default='')
    sent_message = models.ForeignKey(TGMessage, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user']),
            models.Index(fields=['fingerprint']),
        ]
