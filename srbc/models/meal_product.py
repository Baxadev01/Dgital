from django.contrib.auth.models import User

from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('MealProduct', 'MealProductAlias', 'MealProductTag')


class MealProduct(models.Model):
    TYPE_BREAD = 'bread'
    TYPE_FAT = 'fat'
    TYPE_CARB = 'carb'
    TYPE_RAWCARB = 'rawcarb'
    TYPE_FATCARB = 'fatcarb'
    TYPE_PROTEIN = 'protein'
    TYPE_DEADWEIGHT = 'deadweight'
    TYPE_VEG = 'veg'
    TYPE_CARBVEG = 'carbveg'
    TYPE_FRUIT = 'fruit'
    TYPE_DFRUIT = 'dfruit'
    TYPE_DESERT = 'desert'
    TYPE_DRINK = 'drink'
    TYPE_ALCO = 'alco'
    TYPE_UNKNOWN = 'unknown'
    TYPE_UFS = 'ufs'
    TYPE_MIX = 'mix'

    title = models.TextField(verbose_name="Название", max_length=100)

    component_type = models.CharField(max_length=50, verbose_name="Продукт", choices=(
        (TYPE_BREAD, "Хлеб"),
        (TYPE_FAT, "Жирный продукт"),
        (TYPE_CARB, "Готовые углеводы"),
        (TYPE_RAWCARB, "Сухие углеводы"),
        (TYPE_FATCARB, "Жирные углеводы"),
        (TYPE_PROTEIN, "Белковый продукт"),
        (TYPE_DEADWEIGHT, "Балласт"),
        (TYPE_VEG, "Овощи"),
        (TYPE_CARBVEG, "Запасающие овощи"),
        (TYPE_FRUIT, "Фрукты"),
        (TYPE_DFRUIT, "Сухофрукты"),
        (TYPE_DESERT, "Десерт"),
        (TYPE_DRINK, "Калорийный напиток"),
        (TYPE_ALCO, "Алкоголь"),
        (TYPE_UNKNOWN, "Продукт с неопределенным составом"),
        (TYPE_UFS, "Продукт сомнительной питательной ценности"),
        (TYPE_MIX, "Сложная смесь"),
    ), blank=True, default=None, null=True)

    is_verified = models.BooleanField(blank=True, default=False)
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    verified_by = models.ForeignKey(
        User, blank=True, default=None, null=True, on_delete=models.SET_NULL, limit_choices_to={'is_staff': True}
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    language = models.CharField(max_length=2, blank=True, default='ru')

    is_fast_carbs = models.BooleanField(blank=True, default=False, verbose_name='Содержит быстрые углеводы')
    is_alco = models.BooleanField(blank=True, default=False, verbose_name='Содержит алкоголь')

    protein_percent = models.DecimalField(blank=True, default=0, verbose_name='Белки', decimal_places=1, max_digits=4)
    fat_percent = models.DecimalField(blank=True, default=0, verbose_name='Жиры', decimal_places=1, max_digits=4)
    carb_percent = models.DecimalField(blank=True, default=0, verbose_name='Углеводы', decimal_places=1, max_digits=4)

    calories = models.IntegerField(blank=True, null=True, verbose_name="Примерная калорийность (на 100г)")
    alco_prc = models.DecimalField(blank=True, default=0, verbose_name="Содержание алкоголя (%)", decimal_places=1,
                                   max_digits=3)

    glucose_proxy_percent = models.DecimalField(blank=True, default=0, verbose_name="Глюкозный эквивалент (на 100г)",
                                                decimal_places=1, max_digits=3)
    starch_proxy_percent = models.DecimalField(blank=True, default=0, verbose_name="Крахмальный эквивалент (на 100г)",
                                               decimal_places=1, max_digits=3)
    fiber_proxy_percent = models.DecimalField(blank=True, default=0, verbose_name="Клетчаточный эквивалент (на 100г)",
                                              decimal_places=1, max_digits=3)
    protein_proxy_percent = models.DecimalField(blank=True, default=0, verbose_name="Белковый эквивалент (на 100г)",
                                                decimal_places=1, max_digits=3)

    def has_tag(self, tag):
        return self.tags.filter(system_code=tag).exists()

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['component_type']),
            models.Index(fields=['is_fast_carbs']),
            models.Index(fields=['is_alco']),
            models.Index(fields=['starch_proxy_percent']),
            models.Index(fields=['fiber_proxy_percent']),
            models.Index(fields=['glucose_proxy_percent']),
            models.Index(fields=['protein_proxy_percent']),
        ]

        unique_together = (
            ('title', 'language',),
        )

        verbose_name = _('продукт питания')
        verbose_name_plural = _('продукты питания')

    def __str__(self):
        return self.title


class MealProductAlias(models.Model):
    title = models.CharField(verbose_name="Название", max_length=200)
    product = models.ForeignKey(MealProduct, on_delete=models.CASCADE, related_name='aliases')

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.title = self.title.lower()
        super(MealProductAlias, self).save(force_insert, force_update, *args, **kwargs)


class MealProductTag(models.Model):
    title = models.CharField(max_length=255, verbose_name='Тег')
    system_code = models.CharField(max_length=50, unique=True, verbose_name='Код')
    products = models.ManyToManyField(MealProduct, verbose_name='Продукты', blank=True, related_name="tags")
    is_analytical = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = _('тэг продукта')
        verbose_name_plural = _('тэги продуктов')
        indexes = [
            models.Index(fields=['is_analytical']),
        ]

    def __str__(self):
        return self.title
