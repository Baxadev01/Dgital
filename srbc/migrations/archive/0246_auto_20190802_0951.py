# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-08-02 06:51


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0245_auto_20190801_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_meal_analyze_mode_locked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['is_meal_analyze_mode_locked'], name='srbc_profil_is_meal_4e8eb6_idx'),
        ),
    ]
