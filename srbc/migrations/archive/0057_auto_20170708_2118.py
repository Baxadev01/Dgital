# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-08 21:18


import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0056_profile_agreement_signed_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diaryrecord',
            name='faults_list',
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='faults_data',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.jsonb.JSONField(), blank=True, default=[], null=True, size=None),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='meals_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='water_consumed',
            field=srbc.models.DecimalRangeField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
    ]