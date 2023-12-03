from datetime import date

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('TechDutyShift', 'TechDuty')


class TechDutyShift(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

    @property
    def is_current(self):
        return self.start_date <= date.today() <= self.end_date

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return 'Смена %s - %s' % (self.start_date, self.end_date)

    def __repr__(self):
        return '<%s #%s (%s - %s)>' % (self.__class__.__name__, self.pk, self.start_date, self.end_date)


class TechDuty(models.Model):
    techcat = models.ForeignKey(User, limit_choices_to={'groups__name': "TechCat"}, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, limit_choices_to={'groups__name': "Participant"}, related_name='SupervisedUser', on_delete=models.CASCADE
    )
    shift = models.ForeignKey(TechDutyShift, on_delete=models.CASCADE)
    mode = models.CharField(
        max_length=100,
        choices=(
            ('AUTO', _("Дежурный")),
            ('MANUAL', _("Доброволец")),
        ),
        default='AUTO'
    )

    class Meta:
        unique_together = (('techcat', 'user', 'shift'),)
