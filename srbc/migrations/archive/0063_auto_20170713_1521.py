# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-13 15:21


from django.db import migrations, models
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0062_auto_20170713_1104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instagramimage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=srbc.models.ig_upload_to),
        ),
    ]
