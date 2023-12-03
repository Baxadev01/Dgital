from django.contrib.auth.models import User

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext_lazy as _

__all__ = ('UserAdmissionTest',)


class UserAdmissionTest(models.Model):
    user = models.OneToOneField(User, related_name='admission_test', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=100, blank=True,
        choices=(
            ('NOT_STARTED', _("Не дошел")),
            ('IN_PROGRESS', _("В процессе")),
            ('DONE', _("Завершил")),
            ('PASSED', _("Проверено, всё ок")),
            ('FAILED', _("Проверено, завалил")),
            ('REJECTED', _("Отказано")),
            ('ACCEPTED', _("Принят")),

        ),
        default='NOT_STARTED'
    )
    question_asked = models.TextField(blank=True, null=True)
    recommendation_info = models.TextField(blank=True, null=True, verbose_name="Информация о рекоммендателе")
    started_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    reviewed_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return '%s #%s' % (self.__class__.__name__, self.pk)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.pk)


def manage_admission_status(sender, instance, **kwargs):
    application = instance.user.application
    application.admission_status = instance.status
    application.save(update_fields=['admission_status'])


post_save.connect(manage_admission_status, sender=UserAdmissionTest)


def reset_admission_status(sender, instance, **kwargs):
    application = instance.user.application
    application.admission_status = 'NOT_STARTED'
    application.save(update_fields=['admission_status'])


pre_delete.connect(reset_admission_status, sender=UserAdmissionTest)
