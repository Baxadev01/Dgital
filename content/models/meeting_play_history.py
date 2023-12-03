from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .meetings import Meeting

__all__ = ('MeetingPlayHistory',)


class MeetingPlayHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    ip_addr = models.GenericIPAddressField()
    referer_check = models.BooleanField()
    useragent = models.TextField(blank=True)
    item = models.CharField(blank=True, default='playlist', max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['meeting']),
            models.Index(fields=['start_time']),
            models.Index(fields=['ip_addr']),
            models.Index(fields=['referer_check']),
            models.Index(fields=['item']),
        ]
