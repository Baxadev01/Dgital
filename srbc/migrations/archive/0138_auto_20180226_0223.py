# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-25 23:23


from django.db import migrations, models
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0137_srbcimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='srbcimage',
            name='image',
            field=models.ImageField(blank=True, null=True, storage=b'storages.backends.s3boto.S3BotoStorage', upload_to=srbc.models.srbc_image_upload_to),
        ),
    ]
