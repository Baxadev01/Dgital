# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-11 19:02


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0077_auto_20170810_0636'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='telegram_join_code',
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_first_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_is_in_channel',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_last_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
