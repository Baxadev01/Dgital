# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-07-24 20:54


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0236_auto_20190724_2152'),
    ]

    operations = [
        migrations.AddField(
            model_name='mealfault',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
    ]
