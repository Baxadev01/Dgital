# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-22 07:52


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0035_auto_20170922_0926'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dialogue',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
