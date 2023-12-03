from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('Meeting',)


class Meeting(models.Model):
    TYPE_REGULAR = 'REGULAR'
    TYPE_NEWBIE = 'NEWBIE'

    TYPE_UNIT = (
        (TYPE_REGULAR, _('Большой митинг')),
        (TYPE_NEWBIE, _('Новичковый митинг')),
    )

    title = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    delay_days = models.IntegerField(blank=True, default=56)
    description = models.TextField()
    is_uploaded = models.BooleanField(default=False, blank=True)
    is_playable = models.BooleanField(default=False, blank=True)

    type = models.CharField(max_length=100,
                            choices=TYPE_UNIT, default=TYPE_REGULAR)

    status = models.CharField(max_length=50, default='PENDING', choices=(
        ('PENDING', 'Pending'),
        ('UPLOADED', 'Uploaded'),
        ('PROCESSING', 'Processing'),
        ('READY', 'Ready for publication'),
        ('PUBLISHED', 'Published'),
        ('ERROR', 'Error'),
    ))

    duration = models.DurationField(blank=True, null=True, verbose_name="Длительность")
    audio_author = models.CharField(max_length=144, verbose_name="Автор (для мобильного приложения)")
    audio_album = models.CharField(max_length=144, verbose_name="Коллекция/альбом (для мобильного приложения)")

    order_num = models.IntegerField(blank=True, default=99)

    @property
    def playlist(self):
        return "/meetings/%s/playlist.m3u8" % self.pk

    class Meta:
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['is_playable', 'is_uploaded']),
        ]

        verbose_name = _('запись митинга')
        verbose_name_plural = _('записи митингов')
