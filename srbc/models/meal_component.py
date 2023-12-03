from django.db import models

from shared.models import DecimalRangeField
from .diary_meal import DiaryMeal
from .meal_product import MealProduct

__all__ = ('MealComponent',)


class MealComponent(models.Model):
    meal = models.ForeignKey(DiaryMeal, related_name='components', on_delete=models.CASCADE)

    component_type = models.CharField(max_length=50, verbose_name="Продукт", choices=(
        (MealProduct.TYPE_BREAD, "Хлеб"),
        (MealProduct.TYPE_FAT, "Жирный продукт"),
        (MealProduct.TYPE_CARB, "Готовые углеводы"),
        (MealProduct.TYPE_RAWCARB, "Сухие углеводы"),
        (MealProduct.TYPE_FATCARB, "Жирные углеводы"),
        (MealProduct.TYPE_PROTEIN, "Белковый продукт"),
        (MealProduct.TYPE_DEADWEIGHT, "Балласт"),
        (MealProduct.TYPE_VEG, "Овощи"),
        (MealProduct.TYPE_CARBVEG, "Запасающие овощи"),
        (MealProduct.TYPE_FRUIT, "Фрукты"),
        (MealProduct.TYPE_DFRUIT, "Сухофрукты"),
        (MealProduct.TYPE_DESERT, "Десерт"),
        (MealProduct.TYPE_DRINK, "Калорийный напиток"),
        (MealProduct.TYPE_ALCO, "Алкоголь"),
        (MealProduct.TYPE_UNKNOWN, "Продукт с неопределенным составом"),
        (MealProduct.TYPE_MIX, "Сложная смесь"),
    ))

    description = models.TextField(verbose_name="Описание")
    weight = DecimalRangeField(
        decimal_places=3, max_digits=8, max_value=1000, min_value=1,
        verbose_name="Вес или эквивалент"
    )

    is_sweet = models.BooleanField(default=False, blank=True)
    faults_data = models.JSONField(blank=True, null=True, default=list)
    meal_product = models.ForeignKey(MealProduct, blank=True, null=True, on_delete=models.SET_NULL)

    details_protein = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4, verbose_name='Белки')
    details_fat = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4, verbose_name='Жиры')
    details_carb = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4, verbose_name='Углеводы')
    details_sugars = models.BooleanField(blank=True, default=False, verbose_name='Содержит быстрые углеводы')
    other_title = models.CharField(blank=True, null=True, max_length=64, verbose_name='Другое название')
    external_link = models.URLField(blank=True, null=True, max_length=2048, verbose_name='Ссылка на описание продукта')

    @property
    def has_custom_nutrition(self):
        return any(v is not None for v in [self.details_protein, self.details_carb, self.details_fat])

    class Meta:
        indexes = [
            models.Index(fields=['component_type']),
            models.Index(fields=['description']),
            models.Index(fields=['is_sweet']),
        ]
