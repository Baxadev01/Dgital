# Generated by Django 3.1.7 on 2022-01-17 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0221_auto_20211228_1437'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tariff',
            name='fee_eur',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Стоимость (EUR)'),
        ),
        migrations.AlterField(
            model_name='tariff',
            name='fee_rub',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Стоимость (RUB)'),
        ),
    ]