from datetime import datetime, timedelta

from django.db import models
from django.utils.translation import ugettext_lazy as _

from srbc.models.wave import Wave

__all__ = ('Campaign',)


class Campaign(models.Model):
    title = models.CharField(max_length=25)
    start_date = models.DateField()
    mailchimp_group_id = models.CharField(max_length=25, blank=True, null=True)
    is_active = models.BooleanField(blank=True, default=False)
    # is_open = models.BooleanField(blank=True, default=False)
    # is_admission_open = models.BooleanField(blank=True, default=False)

    wave_chat = models.ForeignKey(
        Wave, blank=True, null=True, related_name='chat_campaigns', on_delete=models.SET_NULL
    )
    wave_channel = models.ForeignKey(
        Wave, blank=True, null=True, related_name='channel_campaigns', on_delete=models.SET_NULL
    )

    @property
    def admission_start_date(self):
        if self.start_date:
            return self.start_date - timedelta(days=14)
        else:
            return None

    @property
    def admission_end_date(self):
        if self.start_date:
            return self.start_date - timedelta(days=4)
            # return self.start_date - timedelta(days=8)
        else:
            return None

    @property
    def admission_status(self):
        if self.start_date is None:
            return None

        today = datetime.now().date()
        if today < self.admission_start_date:
            return 'NOT_STARTED'
        if today <= self.admission_end_date:
            return 'IN_PROGRESS'

        return 'ENDED'

    @property
    def is_admission_open(self):
        return self.admission_status == 'IN_PROGRESS'

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return '%s' % self.title

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.title)
