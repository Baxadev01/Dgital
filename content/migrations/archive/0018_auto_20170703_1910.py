# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-03 19:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0017_picture_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='picture',
            name='uid',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
