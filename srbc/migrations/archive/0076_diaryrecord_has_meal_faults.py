# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-08 05:47


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0075_auto_20170807_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord',
            name='has_meal_faults',
            field=models.BooleanField(default=False),
        ),
    ]
