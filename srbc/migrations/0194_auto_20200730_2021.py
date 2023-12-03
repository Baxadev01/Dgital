# Generated by Django 3.0.6 on 2020-07-30 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0193_mealproduct_fiber_percent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mealcomponent',
            name='component_type',
            field=models.CharField(choices=[('bread', 'Хлеб'), ('fat', 'Жирный продукт'), ('carb', 'Готовые углеводы'), ('rawcarb', 'Сухие углеводы'), ('fatcarb', 'Жирные углеводы'), ('protein', 'Белковый продукт'), ('deadweight', 'Балласт'), ('veg', 'Овощи'), ('carbveg', 'Запасающие овощи'), ('fruit', 'Фрукты'), ('dfruit', 'Сухофрукты'), ('desert', 'Десерт'), ('drink', 'Калорийный напиток'), ('alco', 'Алкоголь'), ('unknown', 'Продукт с неопределенным составом'), ('mix', 'Сложная смесь')], max_length=50, verbose_name='Продукт'),
        ),
    ]