import logging
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from shared.models import DecimalRangeField
from .auto_analize_formula import AutoAnalizeFormula

logger = logging.getLogger(__name__)

__all__ = ('ProfileWeightWeekStat', 'ProfileTwoWeekStat',)


class ProfileWeightWeekStat(models.Model):
    user = models.OneToOneField(User, related_name='weight_stat_admin', on_delete=models.DO_NOTHING)
    date_start = models.DateField()
    date_end = models.DateField()
    trueweight_start = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)
    trueweight_end = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)
    weight_start = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)
    weight_end = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'profile_weight_week_stat'


class ProfileTwoWeekStat(models.Model):
    user = models.ForeignKey(User, related_name='two_weeks_stat', on_delete=models.CASCADE)

    date_start = models.DateField()
    date_end = models.DateField()
    trueweight_start = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)
    trueweight_end = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)
    weight_start = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)
    weight_end = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)

    steps_days = models.PositiveIntegerField(blank=True, null=True)
    steps_ok_days = models.PositiveIntegerField(blank=True, null=True)
    overcalory_days = models.PositiveIntegerField(blank=True, null=True)
    ooc_days = models.PositiveIntegerField(blank=True, null=True)
    faulty_days = models.PositiveIntegerField(blank=True, null=True)
    meals_days = models.PositiveIntegerField(blank=True, null=True)
    meals_bad_days = models.PositiveIntegerField(blank=True, null=True)
    alco_days = models.PositiveIntegerField(blank=True, null=True)

    date = models.DateField()  # SRBC-23 дата окончания временного окна
    created_at = models.DateTimeField(auto_now_add=True)

    def formula_debug(self):
        if self.steps_days < 10 or self.meals_days < 10:
            return [round(self.steps_days), round(self.meals_days)]

        result = [
            round(Decimal(self.steps_ok_days) / Decimal(self.steps_days), 2),
            round(Decimal(self.faulty_days) / Decimal(self.meals_days), 2),
            round(Decimal(self.meals_bad_days) / Decimal(self.meals_days), 2),
            round(Decimal(self.overcalory_days) / Decimal(self.meals_days), 2),
            round(Decimal(self.alco_days) / Decimal(self.meals_days), 2),
        ]

        return result

    def formula_core(self):
        if self.steps_days < 10 or self.meals_days < 10:
            return None

        result = []
        if Decimal(self.steps_ok_days) / Decimal(self.steps_days) >= 0.8:
            result.append('1')
        else:
            result.append('0')

        if Decimal(self.faulty_days) / Decimal(self.meals_days) <= 0.2:
            result.append('2')
        else:
            result.append('0')

        if Decimal(self.meals_bad_days) / Decimal(self.meals_days) <= 0.2:
            result.append('3')
        else:
            result.append('0')

        if Decimal(self.overcalory_days) / Decimal(self.meals_days) <= 0.3:
            result.append('4')
        else:
            result.append('0')

        if Decimal(self.alco_days) / Decimal(self.meals_days) <= 0.15:
            result.append('5')
        else:
            result.append('0')

        return "".join(result)

    def forecast(self):
        formula = self.formula_core()
        if formula is None:
            return None

        if formula in ['12345', '12340']:
            return {
                "sign": "gte",
                "coeff": Decimal(0.005),
            }

        if formula in ['12045', '12040']:
            return {
                "sign": "gt",
                "coeff": Decimal(0),
            }

        return {
            "sign": "lte",
            "coeff": Decimal(0),
        }

    def forecast_sign(self):
        dm_coeff = self.dm() / self.trueweight_start

        delta_dates = self.date_end - self.date_start
        delta_days = delta_dates.days + 1

        if dm_coeff < 0:
            return '-'

        # logger.info((delta_days, 0.0025 / 7 * delta_days,))

        if dm_coeff < 0.0025 / 7 * delta_days:
            return '='

        return '+'

    def dm(self):
        return self.trueweight_start - self.trueweight_end

    def dm_control_value(self):
        forecast_control_data = self.forecast()
        if forecast_control_data is None:
            return False

        forecast_control_value = forecast_control_data['coeff'] * self.trueweight_start
        return forecast_control_value

    def forecast_ok(self):
        dm = self.dm()
        forecast_control_data = self.forecast()
        if forecast_control_data is None:
            return False

        forecast_control_value = forecast_control_data['coeff'] * self.trueweight_start

        if forecast_control_data['sign'] == 'gte':
            return dm >= forecast_control_value

        if forecast_control_data['sign'] == 'lte':
            return dm <= forecast_control_value

        if forecast_control_data['sign'] == 'gt':
            return dm > forecast_control_value

    def formula(self):
        core = self.formula_core()
        if core is None:
            return '-'
        return '%s%s' % (self.forecast_sign(), core,)

    @property
    def recommendation(self):
        formula = self.formula()
        recommendation = AutoAnalizeFormula.objects.filter(code=formula).first()
        if not recommendation:
            return AutoAnalizeFormula(comment="Некорректная формула: %s" % formula, attention_required=True)

        return recommendation

    class Meta:
        ordering = ['-date']
        unique_together = (('user', 'date'),)
        indexes = [
            models.Index(fields=['date']),
        ]
