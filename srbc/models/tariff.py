from django.db import models
from django.utils.translation import ugettext_lazy as _

from srbc.utils.helpers import pluralize
from .tariff_group import TariffGroup

__all__ = ('Tariff',)


class Tariff(models.Model):
    DAY = 'DAY'
    WEEK = 'WEEK'
    MONTH = 'MONTH'

    DURATION_UNIT = (
        (DAY, _('Дни')),
        (WEEK, _('Недели')),
        (MONTH, _('Месяцы')),
    )

    slug = models.CharField(max_length=25, blank=True, null=True, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    fee_rub = models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Стоимость (RUB)")
    fee_eur = models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Стоимость (EUR)")

    duration = models.IntegerField(blank=True, null=True, verbose_name="Продолжительность")
    duration_unit = models.CharField(
        max_length=25,
        choices=DURATION_UNIT,
        default=DAY
    )
    tariff_next = models.ForeignKey(
        "self", verbose_name="Следующий тариф", blank=True, null=True, on_delete=models.SET_NULL
    )

    tariff_group = models.ForeignKey(TariffGroup, blank=True, null=True, on_delete=models.SET_NULL)

    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)

    renewal_mode = models.CharField(
        max_length=25,
        choices=(
            ('AUTO', 'Авто-продление'),
            ('APPROVED', 'Авто-подтверждение'),
            ('MANUAL', 'Ручное подтверждение'),
        )
    )

    is_archived = models.BooleanField(default=False, blank=True)

    @property
    def duration_in_days(self):
        # в моей БД почему-то есть записи без этого поля, баг или фича не знаю, добавлю проверку
        if self.duration:
            if self.duration_unit == self.MONTH:
                return self.duration * 30
            elif self.duration_unit == self.WEEK:
                return self.duration * 7
            else:
                return self.duration
        else:
            return 0

    def duration_unit_to_str(self):
        if self.duration_unit == self.DAY:
            return pluralize(self.duration, ['день', 'дня', 'дней'])
        elif self.duration_unit == self.WEEK:
            return pluralize(self.duration, ['неделя', 'недели', 'недель'])
        else:
            return pluralize(self.duration, ['месяц', 'месяца', 'месяцев'])

    def __str__(self):
        return '%s (%0.2f RUB / %0.2f EUR)' % (self.title, self.fee_rub, self.fee_eur)
