# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-22 16:24


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0041_auto_20170622_0838'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_instagram_private',
            field=models.BooleanField(default=False),
        ),
    ]