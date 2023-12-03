from django.contrib.auth.models import User

from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('ParticipationGoal',)


class ParticipationGoal(models.Model):
    STATUS_PROGRESS = 'PROGRESS'
    STATUS_DONE = 'DONE'
    STATUS_ARCHIVED = 'ARCHIVED'

    # описывает цели участников
    STATUSES = (
        (STATUS_PROGRESS, _("Новая")),
        (STATUS_DONE, _("Достигнутая")),
        (STATUS_ARCHIVED, _("Удаленая")),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=144)
    text = models.TextField(null=False, blank=False, max_length=1024)
    status = models.CharField(max_length=32, choices=STATUSES, default=STATUS_PROGRESS)
    created_at = models.DateTimeField(auto_now_add=True)  # дата добавления
    status_changed_at = models.DateTimeField()  # дата последнего изменения статуса
    order_num = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['-created_at']
