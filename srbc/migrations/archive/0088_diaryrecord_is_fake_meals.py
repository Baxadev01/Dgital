# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-31 07:16


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0087_auto_20170828_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord',
            name='is_fake_meals',
            field=models.BooleanField(default=False),
        ),
    ]