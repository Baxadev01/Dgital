import time
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import pre_save
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from shared.models import DecimalRangeField, IntegerRangeField
from .instagram_image import InstagramImage
from .srbc_image import SRBCImage

__all__ = ('DiaryRecord', 'DiaryRecordCopy',)


class DiaryRecord(models.Model):
    PERS_REC_OK = 'OK'
    PERS_REC_F = 'F'
    PERS_REC_NULL = 'NULL'
    PERS_REC_NA = 'NA'

    PERS_REC_CHECK_AUTO = 'AUTO'
    PERS_REC_CHECK_MANUAL = 'MANUAL'

    ANLZ_MODE_NO = 'NO'
    ANLZ_MODE_AUTO = 'ANLZ_AUTO'
    ANLZ_MODE_MANUAL = 'ANLZ_MANUAL'

    OPTIONS_ANLZ_MODE = (
        (ANLZ_MODE_NO, _('Не нужен')),
        (ANLZ_MODE_AUTO, _('Автоматический анализ')),
        (ANLZ_MODE_MANUAL, _('Ручной анализ')),
    )

    MEAL_STATUS_NOT_READY = 'NOT_READY'
    MEAL_STATUS_PENDING = 'PENDING'
    MEAL_STATUS_VALIDATION = 'VALIDATION'
    MEAL_STATUS_FEEDBACK = 'FEEDBACK'
    MEAL_STATUS_DONE = 'DONE'
    MEAL_STATUS_NA_WARN = 'NA_WARN'
    MEAL_STATUS_NA = 'NA'
    MEAL_STATUS_FAKE = 'FAKE'

    MEAL_STATUS_MODE = (
        (MEAL_STATUS_NOT_READY, _("Ожидает заполнения")),
        (MEAL_STATUS_PENDING, _("Ожидает оцифровки")),
        (MEAL_STATUS_VALIDATION, _("Ожидает проверки оцифровки")),
        (MEAL_STATUS_FEEDBACK, _("Ожидает ответа")),
        (MEAL_STATUS_DONE, _("Оцифрован")),
        (MEAL_STATUS_NA_WARN, _("Нет данных, предупреждён")),
        (MEAL_STATUS_NA, _("Нет данных")),
        (MEAL_STATUS_FAKE, _("Данные недостоверны")),
    )

    user = models.ForeignKey(User, related_name='diaries', on_delete=models.CASCADE)
    date = models.DateField(verbose_name='Дата')
    weight = DecimalRangeField(
        decimal_places=3, max_digits=8, blank=True, null=True, max_value=500, min_value=0,
        verbose_name='Вес'
    )
    trueweight = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True, verbose_name='TrueWeight')
    sleep = DecimalRangeField(
        decimal_places=3, max_digits=8, blank=True, null=True, min_value=0, max_value=24,
        verbose_name='Сон'
    )
    steps = IntegerRangeField(blank=True, null=True, min_value=0, max_value=200000, verbose_name='Шаги')
    meals = IntegerRangeField(blank=True, null=True, min_value=0, max_value=10, verbose_name='Полноценность рациона')
    faults = IntegerRangeField(blank=True, null=True, min_value=0, max_value=5)
    meal_image = models.ForeignKey(SRBCImage, limit_choices_to={"role": 'MEAL'}, related_name='diary_record',
                                   null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Коллаж пиемов пищи')
    data_image = models.ForeignKey(InstagramImage, limit_choices_to={"role": 'DATA'}, related_name='diary_record',
                                   blank=True, null=True, on_delete=models.SET_NULL)
    is_pregnant = models.BooleanField(blank=True, default=False)
    is_perfect_weight = models.BooleanField(blank=True, default=False)
    is_sick = models.BooleanField(blank=True, default=False)

    is_meal_validated = models.BooleanField(blank=True, default=False)
    meal_validation_date = models.DateTimeField(blank=True, null=True)
    is_meal_reviewed = models.BooleanField(blank=True, default=False)

    meal_reviewed_by = models.ForeignKey(
        User, related_name="diaries_reviewed", blank=True, null=True, on_delete=models.SET_NULL
    )

    is_overcalory = models.BooleanField(blank=True, default=False)
    is_mono = models.BooleanField(blank=True, default=False)
    is_unload = models.BooleanField(blank=True, default=False)
    is_ooc = models.BooleanField(blank=True, default=False)
    is_na_meals = models.BooleanField(blank=True, default=False)
    is_fake_meals = models.BooleanField(blank=True, default=False)
    is_na_data = models.BooleanField(blank=True, default=False)

    pers_rec_flag = models.CharField(
        max_length=20, verbose_name="Соответствие рекомендациям", default=PERS_REC_NULL,
        choices=(
            (PERS_REC_NULL, 'Не выбрано'),
            (PERS_REC_OK, 'Соответствует'),
            (PERS_REC_F, 'Не соответствует'),
            (PERS_REC_NA, 'Не проверялось'),
        )
    )

    pers_rec_check_mode = models.CharField(
        max_length=20, verbose_name="Режим проверки", default=PERS_REC_CHECK_AUTO,
        choices=(
            (PERS_REC_CHECK_AUTO, 'Автоматический'),
            (PERS_REC_CHECK_MANUAL, 'Ручной'),
        )
    )

    pers_req_faults = ArrayField(models.CharField(max_length=100), blank=True, null=True)

    comment = models.TextField(blank=True, null=True)
    meal_status = models.CharField(
        max_length=50,
        choices=MEAL_STATUS_MODE,
        default=MEAL_STATUS_NOT_READY
    )
    meal_last_status_date = models.DateTimeField(blank=True, null=True)

    # Новые поля, под автооцифровку.
    wake_up_time = models.TimeField(blank=True, null=True, verbose_name='Время пробуждения')
    bed_time = models.TimeField(blank=True, null=True, verbose_name='Время отбоя')
    bed_time_is_next_day = models.BooleanField(blank=True, default=False)

    water_consumed = DecimalRangeField(
        decimal_places=2, max_digits=4, blank=True, null=True, max_value=10, min_value=0,
        verbose_name='Количество потребленной воды'
    )
    dairy_consumed = IntegerRangeField(blank=True, null=True, min_value=0, max_value=5000)
    # meals_data = JSONField(blank=True, null=True, default={})
    faults_data = models.JSONField(blank=True, null=True, default=list)
    has_meal_faults = models.BooleanField(blank=True, default=False)
    meal_self_review = models.BooleanField(blank=True, default=False)

    last_data_updated = models.DateTimeField(blank=True, null=True, verbose_name='Последнее изменение дневных данных')
    last_meal_updated = models.DateTimeField(blank=True, null=True, verbose_name='Последнее изменение рациона')

    last_sleep_updated = models.DateTimeField(
        blank=True, null=True, verbose_name='Последнее изменение данных о времени сна')
    last_steps_updated = models.DateTimeField(
        blank=True, null=True, verbose_name='Последнее изменение данных о пройденных шагах')
    last_weight_updated = models.DateTimeField(blank=True, null=True, verbose_name='Последнее изменение данных о весе')

    anlz_mode = models.CharField(
        max_length=20, blank=True, null=True,
        choices=OPTIONS_ANLZ_MODE,
        default=None
    )

    is_weight_accurate = models.BooleanField(blank=True, null=True, default=True)

    @property
    def wake_up_timestamp(self):
        return datetime.combine(self.date, self.wake_up_time) - timedelta(hours=24)

    @property
    def bed_timestamp(self):
        if not self.bed_time_is_next_day:
            return datetime.combine(self.date, self.bed_time) - timedelta(hours=24)

        return datetime.combine(self.date, self.bed_time)

    @property
    def sleep_text(self):
        if self.sleep is None:
            return None

        sleep = Decimal(int((self.sleep or 0) * 4)) / 4

        sleep_hours = int(sleep)
        sleep_minutes = str(int((sleep - sleep_hours) * 60)).zfill(2)

        return '%s:%s' % (
            sleep_hours,
            sleep_minutes,
        )

    def timespan_calories_check(self, timestamp_start, timestamp_end, calories_treshold):
        meals = self.meals_data.all()
        calories_sum = 0
        for _m in meals:
            if _m.start_timestamp < timestamp_start:
                continue

            if _m.start_timestamp > timestamp_end:
                continue

            if _m.has_carbs:
                return False

            calories_sum += _m.calories_amount

            if calories_sum >= calories_treshold:
                return False

        return True

    @cached_property
    def has_sugar(self):
        # return MealComponent.objects.filter(meal__diary=self, component_type='desert').exists()
        return self.meals_data.filter(
            components__component_type='desert'
        ).exists()

    @cached_property
    def has_alco(self):
        return self.meals_data.filter(
            components__component_type='alco'
        ).exists()
        # return MealComponent.objects.filter(meal__diary=self, component_type='alco').exists()

    @cached_property
    def has_meals(self):
        meals_count = self.meals_data.count()
        # meals_count = DiaryMeal.objects.filter(diary=self).count()
        return meals_count > 0

    @property
    def date_yesterday_text(self):
        return (self.date - timedelta(days=1)).__format__("%d.%m.%Y")

    @property
    def date_text(self):
        return self.date.__format__("%d.%m.%Y")

    @property
    def meal_hashtag(self):
        def digit_to_char(digit):
            if digit < 10:
                return str(digit)
            return chr(ord('A') + digit - 10)

        def str_base(number, base):
            if number < 0:
                return '-' + str_base(-number, base)
            (d, m) = divmod(number, base)
            if d > 0:
                return str_base(d, base) + digit_to_char(m)
            return digit_to_char(m)

        symbols = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        hashlen = 3

        maxnum = 0

        for i in range(1, hashlen + 1):
            maxnum += len(symbols) ** i

        unixtime = int(time.mktime(self.date.timetuple()) / 86400)

        hashnum = (unixtime + int(self.user_id) + int(self.user_id) ** 2 + int(self.user_id) ** 3) % maxnum

        checksymbol = int((hashnum ** 2 + hashnum ** 0.5 + hashnum)) % len(symbols)

        _hash = str_base(hashnum, len(symbols)) + str_base(checksymbol, len(symbols))

        return '#srbc%s' % _hash

    @cached_property
    def get_delta_weights(self):
        """ Получает дельту в весе с начала старта и за вчера.

        :return: дельты весов
        :rtype: (decimal.Decimal, decimal.Decimal) | (None, None)
        """
        diary_last = None
        diary_first = None

        if not self.weight:
            weight_today = None
        else:
            weight_today = self.weight
            diary_first = DiaryRecord.objects.filter(user=self.user, weight__isnull=False). \
                order_by('date').only('weight').first()
            diary_last = DiaryRecord.objects.filter(user=self.user, weight__isnull=False,
                                                    date__lt=self.date).order_by('-date').only('weight').first()
            if not diary_first or not diary_last:
                weight_today = None

        if weight_today:
            weight_delta_yesterday = self.weight - diary_last.weight
            weight_delta_start = self.weight - diary_first.weight
        else:
            weight_delta_yesterday = None
            weight_delta_start = None

        return weight_delta_yesterday, weight_delta_start

    @property
    def meal_short_formula(self):
        """ Подсчитывает данные для фотографии рациона по формуле.
        Формула может быть вида {MEALS}/{FAULTS} , {MEALS}/{FAULTS}* , В/К , N/A или F
        Где
         - MEALS - DiaryRecord.meals
         - FAULTS - DiaryRecord.faults
         - звездочка - при наличии DiaryRecord.is_overcalory
         - В/К - при наличии DiaryRecord.is_ooc
         - N/A - при наличии DiaryRecord.is_na_meals
         - F - при наличии DiaryRecord.is_fake_meals

        :rtype: unicode
        """

        if self.is_ooc:
            result = 'B/K'
        elif self.meal_status == 'FAKE':
            result = 'F'
        elif self.meal_status == 'DONE':
            if self.meals is None and self.faults is None:
                return None

            formula = '{meals}/{faults}{oc}'

            meals = '{meals}0%'.format(meals=self.meals) if self.meals else '--'
            faults = self.faults or 0
            overcalory = '*' if self.is_overcalory else ''
            result = formula.format(meals=meals, faults=faults, oc=overcalory)
        else:
            result = 'N/A'

        return result

    #     models.CharField(
    #     max_length=50,
    #     choices=(
    #         ('WAKETOMEAL', u"Перерыв до завтрака"),
    #         ('FASTSWEET', u"Сладкое натощак"),
    #         ('BREAKTOMEAL', u"Перерыв между приемами пищи"),
    #         ('ALCOFOOD', u"Алкоголь с закуской / Сладкий алкоголь"),
    #         ('ALCO2', u"Большая порция алкоголя"),
    #         ('SWEET2', u"Два сладких приема пищи, отодвинвуших несладкий"),
    #         ('EVENINGSWEET', u"Поздние быстрые углеводы"),
    #         ('LATECARB', u"Поздние углеводы"),
    #         ('FATCARB', u"Жирные углеводы после обеда"),
    #         ('SLEEPCARB', u"Сон после углеводов"),
    #         ('CUMULATIVE', u"Накопительный"),
    #     )
    # ), blank=True, null=True)

    class Meta:
        ordering = ['date']
        unique_together = (('user', 'date'),)
        indexes = [
            models.Index(fields=['user', ]),
            models.Index(fields=['date', ]),
            models.Index(fields=['user', 'steps']),
            models.Index(fields=['user', 'sleep']),
            models.Index(fields=['meal_status']),
            models.Index(fields=['is_fake_meals']),
            models.Index(fields=['meal_last_status_date']),
            models.Index(fields=['meal_reviewed_by']),
        ]


class DiaryRecordCopy(models.Model):
    user = models.ForeignKey(User, related_name='diaries_copy', on_delete=models.CASCADE)
    date = models.DateField()
    weight = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True, max_value=500, min_value=0)
    trueweight = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True)
    sleep = DecimalRangeField(decimal_places=3, max_digits=8, blank=True, null=True, min_value=0, max_value=24)
    steps = IntegerRangeField(blank=True, null=True, min_value=0, max_value=200000)
    meals = IntegerRangeField(blank=True, null=True, min_value=0, max_value=10)
    faults = IntegerRangeField(blank=True, null=True, min_value=0, max_value=5)
    meal_image = models.ForeignKey(InstagramImage, limit_choices_to={"role": 'FOOD'}, related_name='DiaryCopyImageFood',
                                   blank=True, null=True, on_delete=models.SET_NULL)
    data_image = models.ForeignKey(InstagramImage, limit_choices_to={"role": 'DATA'}, related_name='DiaryCopyImageData',
                                   blank=True, null=True, on_delete=models.SET_NULL)
    is_pregnant = models.BooleanField(blank=True, default=False)
    is_perfect_weight = models.BooleanField(blank=True, default=False)
    is_sick = models.BooleanField(blank=True, default=False)
    is_meal_validated = models.BooleanField(blank=True, default=False)
    meal_validation_date = models.DateTimeField(blank=True, null=True)
    is_meal_reviewed = models.BooleanField(blank=True, default=False)
    is_overcalory = models.BooleanField(blank=True, default=False)
    is_mono = models.BooleanField(blank=True, default=False)
    is_unload = models.BooleanField(blank=True, default=False)
    is_ooc = models.BooleanField(blank=True, default=False)
    is_na_meals = models.BooleanField(blank=True, default=False)
    is_fake_meals = models.BooleanField(blank=True, default=False)
    is_na_data = models.BooleanField(blank=True, default=False)
    comment = models.TextField(blank=True, null=True)
    meal_status = models.CharField(
        max_length=50,
        choices=(
            ('NOT_READY', _("Ожидает заполнения")),
            ('PENDING', _("Ожидает оцифровки")),
            ('VALIDATION', _("Ожидает проверки оцифровки")),

            ('FEEDBACK', _("Ожидает ответа")),
            ('DONE', _("Оцифрован")),

            ('NA_WARN', _("Нет данных, предупреждён")),
            ('NA', _("Нет данных")),

            ('FAKE', _("Данные недостоверны")),
        ),
        default='NOT_READY'
    )
    meal_last_status_date = models.DateTimeField(blank=True, null=True)

    # Новые поля, под автооцифровку.
    wake_up_time = models.TimeField(blank=True, null=True)
    bed_time = models.TimeField(blank=True, null=True)
    bed_time_is_next_day = models.BooleanField(blank=True, default=False)

    water_consumed = DecimalRangeField(decimal_places=2, max_digits=4, blank=True, null=True, max_value=10, min_value=0)
    dairy_consumed = IntegerRangeField(blank=True, null=True, min_value=0, max_value=5000)
    # meals_data = JSONField(blank=True, null=True, default={})
    faults_data = models.JSONField(blank=True, null=True, default=list)
    has_meal_faults = models.BooleanField(blank=True, default=False)

    class Meta:
        ordering = ['date']
        unique_together = (('user', 'date'),)
        indexes = [
            models.Index(fields=['user', 'date']),
        ]


def fix_fake_meals_status(sender, instance, **kwargs):
    if instance.is_fake_meals and instance.meal_status != 'FAKE':
        instance.meal_status = 'FAKE'


pre_save.connect(fix_fake_meals_status, sender=DiaryRecord)
