from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('TGChat',)


class TGChat(models.Model):
    code = models.CharField(max_length=6)
    title = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, default=False)
    is_main = models.BooleanField(blank=True, default=True)
    is_moderated = models.BooleanField(blank=True, default=True)
    chat_type = models.CharField(
        choices=(
            ('CHAT', 'Chat'),
            ('CHANNEL', 'Channel'),
        ),
        blank=True,
        max_length=20,
        default='CHAT'
    )

    tg_id = models.CharField(max_length=100, blank=True, null=True)
    tg_slug = models.CharField(max_length=100, blank=True, null=True)

    members = models.ManyToManyField(User, through='TGChatParticipant', related_name='chats')
    next_chat = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '%s %s' % (self.chat_type, self.code)

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['tg_id']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_main']),
            models.Index(fields=['chat_type']),
        ]

        verbose_name = _('чат Telegram')
        verbose_name_plural = _('чаты Telegram')
