# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-05 05:22


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0023_auto_20170729_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='sort_num',
            field=models.SmallIntegerField(blank=True, default=99),
        ),
    ]
