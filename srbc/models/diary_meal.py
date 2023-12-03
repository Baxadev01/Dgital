import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import ugettext_lazy as _

from shared.models import IntegerRangeField
from .diary_record import DiaryRecord

logger = logging.getLogger(__name__)

__all__ = ('DiaryMeal', 'diary_meal_image_upload_to',)


def diary_meal_image_upload_to(instance, filename):
    return os.path.join(
        'diarymeal',
        '%s' % instance.diary_id,
        "%s%s" % (str(uuid4().hex), os.path.splitext(filename)[1])
    )


class DiaryMeal(models.Model):
    IMAGE_STATUS_CORRECT = 'CORRECT'
    IMAGE_STATUS_FAKE_DATE = 'FAKE_DATE'
    IMAGE_STATUS_FAKE_NO_DATE = 'FAKE_NO_DATE'

    IMAGE_STATUS_UNIT = (
        (IMAGE_STATUS_CORRECT, _("Фото за корректный день")),
        (IMAGE_STATUS_FAKE_DATE, _("Фото за некорректный день")),
        (IMAGE_STATUS_FAKE_NO_DATE, _("Фото без EXIF данных")),
    )

    MEAL_TYPE_PREBREAKFAST = "PREBREAKFAST"
    MEAL_TYPE_BREAKFAST = "BREAKFAST"
    MEAL_TYPE_BRUNCH = "BRUNCH"
    MEAL_TYPE_LUNCH = "LUNCH"
    MEAL_TYPE_MERIENDA = "MERIENDA"
    MEAL_TYPE_DINNER = "DINNER"
    MEAL_TYPE_SNACK = "SNACK"
    MEAL_TYPE_SLEEP = "SLEEP"
    MEAL_TYPE_HUNGER = "HUNGER"
    MEAL_TYPE_BLOOD_GLUCOSE = "BLOOD_GLUCOSE"

    MEAL_TYPE_FOODS = [
        MEAL_TYPE_PREBREAKFAST, MEAL_TYPE_BREAKFAST, MEAL_TYPE_BRUNCH, MEAL_TYPE_LUNCH,
        MEAL_TYPE_MERIENDA, MEAL_TYPE_DINNER, MEAL_TYPE_SNACK
    ]

    MEAL_TYPE_UNIT = (
        (MEAL_TYPE_PREBREAKFAST, _("Предзавтрак")),
        (MEAL_TYPE_BREAKFAST, _("Завтрак")),
        (MEAL_TYPE_BRUNCH, _("ВЗ")),
        (MEAL_TYPE_LUNCH, _("Обед")),
        (MEAL_TYPE_MERIENDA, _("Полдник")),
        (MEAL_TYPE_DINNER, _("Ужин")),
        (MEAL_TYPE_SNACK, _("Перекус")),
        (MEAL_TYPE_SLEEP, _("Дневной сон")),
        (MEAL_TYPE_HUNGER, _("Чувство голода")),
        (MEAL_TYPE_BLOOD_GLUCOSE, _("Замер уровня глюкозы в крови")),
    )

    GLUCOSE_UNIT_MEASURE_MG_DL = 'mg/dL'
    GLUCOSE_UNIT_MEASURE_MMOL_L = 'mmol/L'

    GLUCOSE_UNIT_MEASURE_UNIT = (
        (GLUCOSE_UNIT_MEASURE_MG_DL, _("мг/дл")),
        (GLUCOSE_UNIT_MEASURE_MMOL_L, _("ммоль/л")),
    )

    diary = models.ForeignKey(DiaryRecord, related_name='meals_data', on_delete=models.PROTECT)
    start_time = models.TimeField(verbose_name='Время начала')
    start_time_is_next_day = models.BooleanField(default=False, blank=True)
    end_time = models.TimeField(blank=True, null=True, verbose_name='Время завершения')
    end_time_is_next_day = models.BooleanField(default=False, blank=True)
    meal_type = models.CharField(
        max_length=25,
        choices=MEAL_TYPE_UNIT
    )

    meal_image = models.ImageField(upload_to=diary_meal_image_upload_to, blank=True, null=True,
                                   verbose_name='Фото рациона')
    img_meta_data = models.JSONField(blank=True, null=True, default=dict)  # мета-данные фотографии

    meal_image_status = models.CharField(
        max_length=20,
        choices=IMAGE_STATUS_UNIT,
        blank=True,
        default=IMAGE_STATUS_CORRECT
    )

    is_sweet = models.BooleanField(default=False, blank=True, verbose_name='Сахар')
    is_filled = models.BooleanField(default=False, blank=True, verbose_name='Заполнено')
    is_overcalory = models.BooleanField(default=False, blank=True, verbose_name='Избыток калорий')
    scores = IntegerRangeField(default=1, max_value=2, min_value=0, blank=True)
    faults_data = models.JSONField(blank=True, null=True, default=list)

    hunger_intensity = IntegerRangeField(blank=True, max_value=3, min_value=1,
                                         null=True, verbose_name="Интенсивность голода")
    glucose_level = models.DecimalField(blank=True, null=True, decimal_places=2,
                                        max_digits=5, verbose_name='Уровень глюкозы')
    glucose_unit = models.CharField(
        max_length=20,
        choices=GLUCOSE_UNIT_MEASURE_UNIT,
        blank=True,
        default=None,
        null=True
    )

    class Meta:
        permissions = (
            ('manage_diary_meal', 'Manage Diary Meal'),
        )

    @property
    def is_meal(self):
        info_types = [self.MEAL_TYPE_SLEEP, self.MEAL_TYPE_HUNGER, self.MEAL_TYPE_BLOOD_GLUCOSE]
        return self.meal_type not in info_types

    @property
    def start_timestamp(self):
        if not self.start_time_is_next_day:
            return datetime.combine(self.diary.date, self.start_time) - timedelta(hours=24)

        return datetime.combine(self.diary.date, self.start_time)

    @property
    def end_timestamp(self):
        if not self.end_time_is_next_day:
            return datetime.combine(self.diary.date, self.end_time) - timedelta(hours=24)

        return datetime.combine(self.diary.date, self.end_time)

    @property
    def has_slow_carbs(self):
        return self.components.filter(component_type__in=['carb', 'rawcarb', ]).count() > 0

    @property
    def has_starch(self):
        return self.components.filter(component_type__in=['carb', 'rawcarb', 'bread']).count() > 0

    @property
    def has_protein(self):
        return self.components.filter(component_type__in=['protein']).count() > 0

    @property
    def has_fat_carbs(self):
        if self.components.filter(component_type__in=['fatcarb', ]).count() > 0:
            return True

        return False

    @property
    def spirit(self):
        comps = self.components.filter(
            component_type__in=['alco', ]
        ).select_related('meal_product').all()
        return sum([c.weight / Decimal(100) * c.meal_product.alco_prc for c in comps if c.meal_product])

    @property
    def has_fast_carbs(self):
        calories, sugars = self.calories
        return sugars > 1.0

    @property
    def has_carbs(self):
        if self.has_fast_carbs:
            return True

        return self.components.filter(
            component_type__in=['carb', 'rawcarb', 'fatcarb', 'bread', ]
        ).count() > 0

    @property
    def details_fat(self):
        comps = self.components.filter(
            Q(component_type__in=['fat', 'fatcarb']) | Q(meal_product__fat_percent__gt=0)
        )

        total_fat = 0

        for _c in comps:
            if _c.details_fat is not None:
                fat_details = _c.details_fat if _c.details_fat is not None else _c.meal_product.fat_percent
                total_fat += Decimal(_c.weight) / 100 * fat_details
            elif _c.meal_product is not None:
                if _c.meal_product.fat_percent:
                    total_fat += Decimal(_c.weight) / 100 * _c.meal_product.fat_percent
                elif _c.meal_product.component_type in ['fat', 'fatcarb']:
                    total_fat += _c.weight

        return total_fat

    def components_weight_by_type(self, component_types):
        res = self.components.filter(
            component_type__in=component_types
        ).aggregate(total_weight=Sum('weight'))

        return res.get('total_weight', 0) or 0

    @property
    def has_calories(self):
        total_calories, has_sugars = self.calories

        return total_calories > 0

    @property
    def savory_calories(self):
        total_calories = 0
        comps = self.components.select_related('meal_product').all()
        for _c in comps:
            if not _c.meal_product:
                if _c.details_carb is None:
                    continue
                elif _c.details_sugars:
                    continue

                details_carb = _c.details_carb or 0
                details_fat = _c.details_fat or 0
                details_prot = _c.details_protein or 0

                total_calories += Decimal(details_carb * 4 + details_prot * 4 + details_fat * 8) / 100 * _c.weight
            elif _c.meal_product.component_type in ['unknown', 'mix']:
                if _c.details_carb is None:
                    if _c.meal_product.is_fast_carbs:
                        continue

                    details_carb = _c.meal_product.carb_percent or 0
                    details_fat = _c.meal_product.fat_percent or 0
                    details_prot = _c.meal_product.protein_percent or 0
                else:
                    if _c.details_sugars:
                        continue

                    details_carb = _c.details_carb or 0
                    details_fat = _c.details_fat or 0
                    details_prot = _c.details_protein or 0

                total_calories += Decimal(details_carb * 4 + details_prot * 4 + details_fat * 8) / 100 * _c.weight
            else:
                if _c.meal_product.is_fast_carbs:
                    continue

                total_calories += Decimal(_c.meal_product.calories) / 100 * _c.weight

        return total_calories

    @property
    def calories(self):
        total_calories = 0
        has_sugars = 0
        comps = self.components.select_related('meal_product').all()
        for _c in comps:
            if _c.meal_product is None or _c.meal_product.component_type in ['unknown', 'mix']:
                if _c.details_carb is None:
                    if _c.meal_product:
                        if _c.meal_product.is_fast_carbs:
                            if _c.meal_product.glucose_proxy_percent:
                                has_sugars += _c.meal_product.glucose_proxy_percent / 100 * _c.weight
                            else:
                                has_sugars += Decimal(99) / 100 * _c.weight

                        details_carb = _c.meal_product.carb_percent or 0
                        details_fat = _c.meal_product.fat_percent or 0
                        details_prot = _c.meal_product.protein_percent or 0
                    else:
                        has_sugars += Decimal(99) / 100 * _c.weight
                        continue
                else:
                    if _c.details_sugars:
                        has_sugars += Decimal(99) / 100 * _c.weight

                    details_carb = _c.details_carb or 0
                    details_fat = _c.details_fat or 0
                    details_prot = _c.details_protein or 0

                total_calories += Decimal(details_carb * 4 + details_prot * 4 + details_fat * 8) / 100 * _c.weight
            else:
                if _c.meal_product.is_fast_carbs:
                    if _c.meal_product.glucose_proxy_percent:
                        has_sugars += _c.meal_product.glucose_proxy_percent / 100 * _c.weight
                    else:
                        has_sugars += Decimal(99) / 100 * _c.weight

                total_calories += Decimal(_c.meal_product.calories) / 100 * _c.weight

        return total_calories, has_sugars

    @property
    def calories_amount(self):
        calories, sugars = self.calories
        return calories

    @property
    def is_proper_meal(self):
        return self.savory_calories >= 50

    def is_substantial(self, calories_treshold=0):
        total_calories = 0
        comps = self.components.select_related('meal_product').all()

        if self.has_carbs:
            return True

        if self.has_fast_carbs:
            return True

        for _c in comps:
            if _c.meal_product is None or _c.meal_product.component_type is None:
                if _c.details_carb is None:
                    return True

                if _c.details_sugars:
                    return True

                details_carb = _c.details_carb or 0
                details_fat = _c.details_fat or 0
                details_prot = _c.details_protein or 0

                total_calories += Decimal(details_carb * 4 + details_prot * 4 + details_fat * 8) / 100 * _c.weight

            elif _c.meal_product.component_type in ['unknown', 'mix']:
                if _c.details_carb is None:
                    if _c.meal_product.is_fast_carbs:
                        return True

                    details_carb = _c.meal_product.carb_percent or 0
                    details_fat = _c.meal_product.fat_percent or 0
                    details_prot = _c.meal_product.protein_percent or 0
                else:
                    details_carb = _c.details_carb or 0
                    details_fat = _c.details_fat or 0
                    details_prot = _c.details_protein or 0

                total_calories += Decimal(details_carb * 4 + details_prot * 4 + details_fat * 8) / 100 * _c.weight
            else:
                total_calories += Decimal(_c.meal_product.calories) / 100 * _c.weight

            if total_calories >= calories_treshold:
                return True

        return False

    @property
    def is_alco(self):
        return self.components.filter(component_type__in=['alco']).count() > 0

    def save(self, *args, **kwargs):
        # delete old file when replacing by updating the file
        try:
            this = DiaryMeal.objects.get(id=self.id)
            if this.meal_image != self.meal_image:
                this.meal_image.delete(save=False)

        except:
            pass  # when new meal is creating then we do nothing, normal case
        super(DiaryMeal, self).save(*args, **kwargs)

    @property
    def image_exif_datetime(self):
        """ Возвращает дату фото по его EXIF данным

        :return: datetime.date
        """
        if self.img_meta_data:
            img_date = self.img_meta_data.get('DateTime') or self.img_meta_data.get('DateTimeOriginal')

            if not img_date:
                return None

            try:
                img_date = datetime.strptime(img_date, '%Y:%m:%d %H:%M:%S')
            except Exception as exc:
                try:
                    # дополнительно проверим на ISO формат
                    img_date = datetime.fromisoformat(img_date)
                except Exception as exc:
                    # в sentry увидим ошибку, но оставим функционал рабочим
                    logger.exception(exc)
                    return None
                else:
                    return img_date
            else:
                return img_date
        else:
            return None
