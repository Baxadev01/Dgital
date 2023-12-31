# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-03 19:05


import content.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0015_auto_20170702_2030'),
    ]

    operations = [
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('image', models.ImageField(blank=True, null=True, upload_to=content.models.picture_upload_to)),
            ],
        ),
    ]
