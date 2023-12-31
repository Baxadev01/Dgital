# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-22 07:38


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_meeting_type'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='meeting',
            index=models.Index(fields=['date'], name='content_mee_date_c08d45_idx'),
        ),
        migrations.AddIndex(
            model_name='meeting',
            index=models.Index(fields=['is_playable', 'is_uploaded'], name='content_mee_is_play_d4521a_idx'),
        ),
        migrations.AddIndex(
            model_name='basics',
            index=models.Index(fields=['keyword', 'type'], name='content_bas_keyword_2e30f3_idx'),
        ),
    ]
