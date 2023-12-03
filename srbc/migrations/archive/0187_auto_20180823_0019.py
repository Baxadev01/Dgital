# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-08-22 21:19


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0186_auto_20180822_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='mealproduct',
            name='carb_percent',
            field=models.FloatField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='mealproduct',
            name='fat_percent',
            field=models.FloatField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='mealproduct',
            name='ingredients',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mealproduct',
            name='is_alco',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='mealproduct',
            name='is_fast_carbs',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='mealproduct',
            name='protein_percent',
            field=models.FloatField(blank=True, default=0),
        ),
    ]
