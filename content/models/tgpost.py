from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .tgchat import TGChat

__all__ = ('TGPost',)


class TGPost(models.Model):
    author = models.ForeignKey(User, related_name='posts_by', on_delete=models.CASCADE, limit_choices_to={
        'groups__name__startswith': "ChannelAdmin",
    })
    text = models.TextField()
    created_at = models.DateTimeField()
    posted_at = models.DateTimeField(blank=True, null=True)
    channel = models.ForeignKey(TGChat, blank=True, null=True, on_delete=models.CASCADE)
    # wave = models.ForeignKey(Wave, blank=True, null=True)
    message_id = models.BigIntegerField(blank=True, null=True)
    image_url = models.CharField(blank=True, null=True, max_length=1024)
    is_private = models.BooleanField(default=False, blank=True)
    is_global = models.BooleanField(default=False, blank=True)
    is_posted = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return 'Telegram Post #%s' % self.pk

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['posted_at']),
            models.Index(fields=['author']),
            models.Index(fields=['is_private']),
            models.Index(fields=['is_global']),
            models.Index(fields=['is_posted']),
        ]
        verbose_name = _('сообщение в канале')
        verbose_name_plural = _('сообщения в канале')
