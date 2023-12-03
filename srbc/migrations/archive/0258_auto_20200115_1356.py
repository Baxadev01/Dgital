# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2020-01-15 10:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0257_mealproduct_starch_percent'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='diaryrecord',
            name='srbc_diaryr_user_id_18de8d_idx',
        ),
        migrations.AddIndex(
            model_name='diaryrecord',
            index=models.Index(fields=['user'], name='srbc_diaryr_user_id_6b601a_idx'),
        ),
        migrations.AddIndex(
            model_name='diaryrecord',
            index=models.Index(fields=['date'], name='srbc_diaryr_date_6ccf8a_idx'),
        ),
    ]