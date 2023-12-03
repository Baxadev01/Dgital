from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _

from shared.models import ChoiceArrayField
from .utils import checkpoint_image_upload_to

__all__ = ('Checkpoint', 'CheckpointPhotos', 'checkpoint_face_image_upload_to',
           'checkpoint_rear_image_upload_to', 'checkpoint_side_image_upload_to',)


def checkpoint_face_image_upload_to(instance, filename):
    return checkpoint_image_upload_to(instance=instance, field='face', filename=filename)


def checkpoint_side_image_upload_to(instance, filename):
    return checkpoint_image_upload_to(instance=instance, field='side', filename=filename)


def checkpoint_rear_image_upload_to(instance, filename):
    return checkpoint_image_upload_to(instance=instance, field='rear', filename=filename)


class Checkpoint(models.Model):
    user = models.ForeignKey(User, related_name='checkpoints', on_delete=models.CASCADE)
    date = models.DateField()  # дата замеров
    last_update = models.DateTimeField(null=True)  # дата последнего изменения замеров

    is_editable = models.BooleanField(blank=True, default=True)
    is_measurements_done = models.BooleanField(blank=True, default=False)
    is_photo_done = models.BooleanField(blank=True, default=False)

    # (DEV-69) контрольные замеры, в мм
    measurement_point_01 = models.IntegerField(blank=True, null=True)
    measurement_point_02 = models.IntegerField(blank=True, null=True)
    measurement_point_03 = models.IntegerField(blank=True, null=True)
    measurement_point_04 = models.IntegerField(blank=True, null=True)
    measurement_point_05 = models.IntegerField(blank=True, null=True)
    measurement_point_06 = models.IntegerField(blank=True, null=True)
    measurement_point_07 = models.IntegerField(blank=True, null=True)
    measurement_point_08 = models.IntegerField(blank=True, null=True)
    measurement_point_09 = models.IntegerField(blank=True, null=True)
    measurement_point_10 = models.IntegerField(blank=True, null=True)
    measurement_point_11 = models.IntegerField(blank=True, null=True)
    measurement_point_12 = models.IntegerField(blank=True, null=True)
    measurement_point_13 = models.IntegerField(blank=True, null=True)
    measurement_point_14 = models.IntegerField(blank=True, null=True)
    measurement_point_15 = models.IntegerField(blank=True, null=True)
    measurement_point_16 = models.IntegerField(blank=True, null=True)
    measurement_height = models.IntegerField(blank=True, null=True)

    @property
    def measurements_sum(self):
        if not self.is_measurements_done:
            return None

        return self.measurement_point_01 + \
               self.measurement_point_02 + \
               self.measurement_point_03 + \
               self.measurement_point_04 + \
               self.measurement_point_05 + \
               self.measurement_point_06 + \
               self.measurement_point_07 + \
               self.measurement_point_08 + \
               self.measurement_point_09 + \
               self.measurement_point_10 + \
               self.measurement_point_11 + \
               self.measurement_point_12 + \
               self.measurement_point_13 + \
               self.measurement_point_14 + \
               self.measurement_point_15 + \
               self.measurement_point_16

    @property
    def is_filled(self):
        return self.measurement_point_01 is not None \
               and self.measurement_point_02 is not None \
               and self.measurement_point_03 is not None \
               and self.measurement_point_04 is not None \
               and self.measurement_point_05 is not None \
               and self.measurement_point_06 is not None \
               and self.measurement_point_07 is not None \
               and self.measurement_point_08 is not None \
               and self.measurement_point_09 is not None \
               and self.measurement_point_10 is not None \
               and self.measurement_point_11 is not None \
               and self.measurement_point_12 is not None \
               and self.measurement_point_13 is not None \
               and self.measurement_point_14 is not None \
               and self.measurement_point_15 is not None \
               and self.measurement_point_16 is not None \
               and self.measurement_height is not None

    class Meta:
        indexes = [
            models.Index(fields=['user', 'date'], name="idx_checkpoint_user_date"),
        ]

        unique_together = (
            ('user', 'date',),
        )
        verbose_name = _('контрольные замеры')
        verbose_name_plural = _('контрольные замеры')


class CheckpointPhotos(models.Model):
    REJECTION_REASON_CHOICES = (
        ('CLOTHES', 'Неудачная одежда (леггинсы, футболки, слитный купальник и т.д.)'),
        ('CUTOFF', 'Обрезаны части тела (нет ног-головы)'),
        ('ANGLE', 'Неправильный ракурс (сверху вниз или снизу вверх)'),
        ('POSE', 'Неправильныая поза (три четверти вместо анфас и т.п., руки закрывают изгиб спины)'),
        ('LIGHT', 'Недостаточная освещенность-контрастность (снято в темноте, снято против света)'),
        ('BACKGROUND', 'Неправильный фон (очень пестрый)'),
        ('BLUR', 'Фотографии не в фокусе (изображение размыто)'),
    )
    checkpoint = models.ForeignKey(Checkpoint, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, related_name='checkpoint_photos', on_delete=models.CASCADE)
    date = models.DateField()
    front_image = models.ImageField(upload_to=checkpoint_face_image_upload_to, blank=True, null=True)
    side_image = models.ImageField(upload_to=checkpoint_side_image_upload_to, blank=True, null=True)
    rear_image = models.ImageField(upload_to=checkpoint_rear_image_upload_to, blank=True, null=True)
    crop_meta = models.JSONField(blank=True, null=True, default=dict)
    status = models.CharField(
        default='NEW', max_length=20, choices=(
            ('NEW', "На обработке"),
            ('APPROVED', "Одобрены"),
            ('REJECTED', "Отклонены"),
        )
    )

    rejection_comment = models.TextField(blank=True, null=True)
    rejection_reasons = ChoiceArrayField(
        models.CharField(
            max_length=50,
            choices=REJECTION_REASON_CHOICES
        ),
        default=list,
        blank=True
    )

    def save(self, *args, **kwargs):
        # delete old file when replacing by updating the file
        try:
            this = CheckpointPhotos.objects.get(id=self.id)
            if this.front_image != self.front_image:
                this.front_image.delete(save=False)
            if this.side_image != self.side_image:
                this.side_image.delete(save=False)
            if this.rear_image != self.rear_image:
                this.rear_image.delete(save=False)

        except ObjectDoesNotExist:
            pass  # when new photo then we do nothing, normal case
        super(CheckpointPhotos, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('контрольные фото')
        verbose_name_plural = _('контрольные фото')
