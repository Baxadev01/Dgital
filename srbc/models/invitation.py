from django.contrib.auth.models import User
from django.db import models

from .wave import Wave

__all__ = ('Invitation',)


class Invitation(models.Model):
    code = models.CharField(max_length=100, unique=True)
    expiring_at = models.DateTimeField(blank=True, null=True)
    is_applied = models.BooleanField(default=False, blank=True)
    applied_at = models.DateTimeField(blank=True, null=True)
    applied_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    wave = models.ForeignKey(Wave, blank=True, null=True, on_delete=models.CASCADE)
    club_only = models.BooleanField(default=False, blank=True)
    communication_mode = models.CharField(
        max_length=20, blank=True, null=True,
        choices=(
            ('CHANNEL', "Канал"),
            ('CHAT', "Чат"),
        )
    )
    days_paid = models.IntegerField()
