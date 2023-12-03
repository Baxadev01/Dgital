from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .tgpost import TGPost

__all__ = ('TGMessage',)


class TGMessage(models.Model):
    TYPE_QUESTION = 'QUESTION'
    TYPE_FORMULA = 'FORMULA'
    TYPE_MEAL = 'MEAL'
    TYPE_FEEDBACK = 'FEEDBACK'

    text = models.TextField()
    author = models.ForeignKey(User, related_name='questions_by', on_delete=models.SET_NULL, null=True)
    assigned = models.ForeignKey(
        User, related_name='questions_for', null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'groups__name': "ChannelAdmin"}
    )
    created_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=(
        ("NEW", "Новый"),
        ("REJECTED", "Отклонён"),
        ("CANCELED", "Отменён"),
        ("ANSWERED", "Отвечен"),
        ("POSTPONED", "Отложен"),
    ), default="NEW")
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User, related_name='resolved_by', null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'groups__name': "ChannelAdmin"}
    )

    answer = models.ForeignKey(TGPost, related_name='answers_to', null=True, blank=True, on_delete=models.SET_NULL)
    tg_message_id = models.IntegerField(blank=True, null=True)
    message_type = models.CharField(
        max_length=100,
        choices=(
            ("QUESTION", "Вопрос"),
            ("FEEDBACK", "Отзыв"),
            ("MEAL", "Рацион"),
            ("FORMULA", "Формула"),
        )
    )

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['resolved_at']),
            models.Index(fields=['resolved_by']),
            models.Index(fields=['status']),
            models.Index(fields=['author']),
            models.Index(fields=['assigned']),
            models.Index(fields=['answer']),
            models.Index(fields=['message_type']),
        ]

        verbose_name = _('сообщение чатботу')
        verbose_name_plural = _('сообщения чатботу')
