# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-11-01 02:20


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0253_merge_20191101_0520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mealproductmoderation',
            name='meal_component',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='srbc.MealComponent'),
        ),
    ]
