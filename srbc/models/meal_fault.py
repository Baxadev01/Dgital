from django.db import models

__all__ = ('MealFault',)


class MealFault(models.Model):
    title = models.CharField(max_length=250)
    short_title = models.CharField(max_length=250, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    code = models.CharField(max_length=25, unique=True, blank=True, null=True)
    is_active = models.BooleanField(blank=True, default=True)
    is_public = models.BooleanField(blank=True, default=True)
    is_manual = models.BooleanField(blank=True, default=False)
    scopes = models.JSONField(blank=True, default=list)

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['code']),
        ]
