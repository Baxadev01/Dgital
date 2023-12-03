from django.db import models

from content.models.tgchat import TGChat

__all__ = ('Wave',)


class Wave(models.Model):
    title = models.CharField(max_length=25)
    start_date = models.DateField()
    is_in_club = models.BooleanField(default=False, blank=True)
    is_archived = models.BooleanField(default=False, blank=True)
    starting_chat = models.ForeignKey(TGChat, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['is_in_club']),
            models.Index(fields=['is_archived']),
        ]

    def __str__(self):
        return '%s' % self.title

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.title)
