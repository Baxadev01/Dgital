
from django.db import models

from .diary_record import DiaryRecord

__all__ = ('DiaryRecordAnalysis', )


class DiaryRecordAnalysis(models.Model):
    diary = models.OneToOneField(DiaryRecord, related_name='analysis', on_delete=models.CASCADE)

    containers = models.JSONField(blank=True, null=True, default=list)

    day_stat = models.JSONField(blank=True, null=True, default=list)


