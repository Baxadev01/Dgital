# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-12-24 10:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0259_auto_20191217_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mealproductalias',
            name='title',
            field=models.CharField(max_length=200, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
        ),
    ]