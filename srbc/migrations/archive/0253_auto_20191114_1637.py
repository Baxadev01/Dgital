# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-11-14 13:37


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0252_auto_20190930_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='usernote',
            name='adjust_carb_sub_breakfast',
            field=models.BooleanField(default=False),
        ),
    ]
