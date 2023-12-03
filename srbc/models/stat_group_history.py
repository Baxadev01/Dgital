from django.contrib.auth.models import User

from django.db import models

__all__ = ('StatGroupHistory',)


class StatGroupHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stat_group = models.CharField(
        max_length=30,
        choices=(
            ('INCLUDE_MAIN', 'INCLUDE_MAIN',),
            ('INCLUDE_GENERAL', 'INCLUDE_GENERAL',),
            ('INCLUDE_BASELINE', 'INCLUDE_BASELINE',),
            ('EXCLUDE_REQUESTED', 'EXCLUDE_REQUESTED',),
            ('EXCLUDE_REQUESTED_TMP', 'EXCLUDE_REQUESTED_TMP',),
            ('EXCLUDE_FORCED', 'EXCLUDE_FORCED',),
            ('EXCLUDE_FORCED_REANIMATED', 'EXCLUDE_FORCED_REANIMATED',),
        ),
    )

    active_from = models.DateField(blank=True, null=True)
    active_until = models.DateField(blank=True, null=True)
