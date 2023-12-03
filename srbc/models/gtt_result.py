import os
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .user_note import UserNote
from .utils import checkpoint_image_upload_to

__all__ = ('GTTResult', 'gtt_image_upload_to_1', 'gtt_image_upload_to_2', 'gtt_image_upload_to_3',)


def gtt_image_upload_to(instance, field, filename):
    return os.path.join(
        'gtt',
        '%s' % instance.user_id,
        instance.date.strftime('%Y-%m-%d'),
        "%s-%s%s" % (field, str(uuid4().hex), os.path.splitext(filename)[1])
    )


def gtt_image_upload_to_1(instance, filename):
    return checkpoint_image_upload_to(instance=instance, field='1', filename=filename)


def gtt_image_upload_to_2(instance, filename):
    return checkpoint_image_upload_to(instance=instance, field='2', filename=filename)


def gtt_image_upload_to_3(instance, filename):
    return checkpoint_image_upload_to(instance=instance, field='3', filename=filename)


class GTTResult(models.Model):
    user = models.ForeignKey(User, related_name="gtt_results", on_delete=models.CASCADE)
    date = models.DateField()
    date_added = models.DateTimeField(auto_now_add=True)
    glucose_unit = models.CharField(
        max_length=50,
        choices=(
            ('MG_DL', _("мг/дл")),
            ('MM_L', _("ммоль/л")),
        ),
    )

    glucose_express = models.FloatField(blank=True, null=True)
    glucose_0 = models.FloatField(blank=True, null=True)
    glucose_60 = models.FloatField(blank=True, null=True)
    glucose_120 = models.FloatField(blank=True, null=True)
    insulin_0 = models.FloatField(blank=True, null=True)
    insulin_60 = models.FloatField(blank=True, null=True)
    insulin_120 = models.FloatField(blank=True, null=True)
    homa_index = models.FloatField(blank=True, null=True)

    status = models.CharField(
        max_length=50,
        choices=(
            ('NEW', _("Новый")),
            ('DOC', _("Ожидает медицинского анализа")),
            ('MEAL', _("Ожидает корректировки рациона")),
            ('DONE', _("Проанализирован")),
        ),
        default='NEW'
    )

    image_1 = models.ImageField(upload_to=gtt_image_upload_to_1, blank=True, null=True)
    image_2 = models.ImageField(upload_to=gtt_image_upload_to_2, blank=True, null=True)
    image_3 = models.ImageField(upload_to=gtt_image_upload_to_3, blank=True, null=True)

    medical_resolution = models.TextField(blank=True, null=True, verbose_name="Диагноз")
    medical_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий врача")
    meal_comment = models.TextField(blank=True, null=True, verbose_name="Корректировка рациона")

    is_reviewed = models.BooleanField(blank=True, default=False)
    user_note_doc = models.ForeignKey(UserNote, blank=True, null=True, on_delete=models.SET_NULL,
                                      related_name="gtt_doc")
    user_note_meal = models.ForeignKey(UserNote, blank=True, null=True, on_delete=models.SET_NULL,
                                       related_name="gtt_meal")

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.glucose_unit == 'MG_DL':
            self.glucose_unit = 'MM_L'
            self.glucose_0 *= 0.05509642
            self.glucose_60 *= 0.05509642
            self.glucose_120 *= 0.05509642

        self.homa_index = self.glucose_0 * self.insulin_0 / 22.5

        if self.user_note_doc is None:
            self.user_note_doc = UserNote(
                user=self.user,
                author_id=settings.SYSTEM_USER_ID,
                label='DOC',
                date_added=self.date_added,
                is_published=False
            )

        gtt_note_content = "[Результаты ГТТ](/admin/srbc/gttresult/%s/) от %s:\n\n" % (
            self.pk,
            self.date.__format__('%d.%m.%Y')
        )

        if self.glucose_express:
            gtt_note_content += "**Экспресс-анализ на глюкозу:** %s\n\n" % self.glucose_express

        gtt_note_content += "**Глюкоза** (0 - 60 - 120): %10.1f - %10.1f - %10.1f\n\n" % (
            self.glucose_0,
            self.glucose_60,
            self.glucose_120,
        )

        gtt_note_content += "**Инсулин** (0 - 60 - 120): %10.1f - %10.1f - %10.1f\n\n" % (
            self.insulin_0,
            self.insulin_60,
            self.insulin_120,
        )

        gtt_note_content += "**Индекс HOMA:** %10.4f\n\n" % self.homa_index

        if self.medical_resolution:
            gtt_note_content += "**Диагноз:** %s\n\n" % self.medical_resolution

        if self.medical_comment:
            gtt_note_content += "**Комментарий врача:** %s" % self.medical_comment

        self.user_note_doc.content = gtt_note_content
        self.user_note_doc.save()

        self.user_note_doc_id = self.user_note_doc.pk

        if update_fields is not None:
            fields_to_update = update_fields + ['user_note_doc', 'user_note_meal', 'homa_index', 'glucose_unit']
        else:
            fields_to_update = None

        super(GTTResult, self).save(force_insert, force_update, using, fields_to_update)
