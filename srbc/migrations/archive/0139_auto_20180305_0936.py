# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-05 06:36


from django.db import migrations, models
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0138_auto_20180226_0223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='srbcimage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=srbc.models.srbc_image_upload_to),
        ),
    ]
