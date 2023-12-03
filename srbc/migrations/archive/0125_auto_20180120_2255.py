# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-20 19:55


from django.db import migrations, models
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0124_auto_20180120_2229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='city',
            field=models.CharField(max_length=100, null=True, verbose_name='\u0413\u043e\u0440\u043e\u0434'),
        ),
        migrations.AlterField(
            model_name='application',
            name='country',
            field=models.CharField(max_length=100, null=True, verbose_name='\u0421\u0442\u0440\u0430\u043d\u0430'),
        ),
        migrations.AlterField(
            model_name='application',
            name='height',
            field=models.IntegerField(null=True, verbose_name='\u0412\u0430\u0448 \u0440\u043e\u0441\u0442'),
        ),
        migrations.AlterField(
            model_name='application',
            name='weight',
            field=srbc.models.DecimalRangeField(decimal_places=3, max_digits=8, null=True, verbose_name='\u0412\u0430\u0448 \u0442\u0435\u043a\u0443\u0449\u0438\u0439 (\u0441\u0442\u0430\u0440\u0442\u043e\u0432\u044b\u0439) \u0432\u0435\u0441'),
        ),
    ]
