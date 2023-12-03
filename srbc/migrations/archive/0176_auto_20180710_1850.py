# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-10 15:50


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0175_auto_20180710_1517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='srbcimage',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photo_stream', to=settings.AUTH_USER_MODEL),
        ),
    ]