# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-09 06:57


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0102_profile_is_self_meal_formula'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord',
            name='meal_validation_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]