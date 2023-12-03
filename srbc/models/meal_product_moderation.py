from django.contrib.auth.models import User
from django.db import models

from .meal_component import MealComponent
from .meal_product import MealProduct

__all__ = ('MealProductModeration',)


class MealProductModeration(models.Model):
    meal_component = models.ForeignKey(MealComponent, on_delete=models.SET_NULL, null=True)
    moderator = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=50, choices=(
        ('PENDING', 'Ожидает модерации'),
        ('APPROVED_NEW', 'Новый продукт'),
        ('APPROVED_ALIAS', 'Синоним'),
        ('REJECTED_REMOVE', 'Отклонено - удалить из рациона'),
        ('REJECTED_IGNORE', 'Отклонено - игнорировать'),
        ('REJECTED_REPLACE', 'Отклонено - заменить продукт в рационе'),
    ), default='PENDING')

    component_type = models.CharField(max_length=50, verbose_name="Продукт", choices=(
        ('bread', "Хлеб"),
        ('fat', "Жирный продукт"),
        ('carb', "Готовые углеводы"),
        ('rawcarb', "Сухие углеводы"),
        ('fatcarb', "Жирные углеводы"),
        ('protein', "Белковый продукт"),
        ('deadweight', "Балласт"),
        ('veg', "Овощи"),
        ('carbveg', "Запасающие овощи"),
        ('fruit', "Фрукты"),
        ('dfruit', "Сухофрукты"),
        ('desert', "Десерт"),
        ('drink', "Калорийный напиток"),
        ('alco', "Алкоголь"),
        ('unknown', "Продукт с неопределенным составом"),
        ('mix', "Сложная смесь"),
    ), blank=True, default=None, null=True)

    title_source = models.CharField(max_length=1024)
    title = models.CharField(max_length=100)

    rejection_reason = models.TextField(blank=True, null=True)

    alias_of = models.ForeignKey(MealProduct, blank=True, null=True, on_delete=models.SET_NULL)

    added_at = models.DateTimeField(auto_now_add=True)
    moderated_at = models.DateTimeField(blank=True, null=True)
