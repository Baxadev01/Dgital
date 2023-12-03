from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('Dialogue',)


class Dialogue(models.Model):
    user = models.ForeignKey(User, related_name='dialogue_messages', blank=True, null=True, on_delete=models.SET_NULL)
    tg_user_id = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_incoming = models.BooleanField()
    answered_by = models.ForeignKey(
        User, related_name='dialogue_answers', null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'is_staff': True}
    )

    is_markdown = models.BooleanField(blank=True, default=True)
    tg_message_id = models.IntegerField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['answered_by']),
            models.Index(fields=['user']),
            models.Index(fields=['tg_user_id']),
            models.Index(fields=['is_incoming']),
        ]

        verbose_name = _('диалог')
        verbose_name_plural = _('диалоги')
