# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-10-21 14:19


import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0251_merge_20191021_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mealproduct',
            name='aliases',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, default=[], size=None),
        ),
        migrations.AlterField(
            model_name='mealproduct',
            name='title',
            field=models.TextField(max_length=100, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
        ),
        migrations.AlterField(
            model_name='mealproductmoderation',
            name='title',
            field=models.CharField(max_length=100),
        )
    ]
