# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-09-07 05:29


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0066_auto_20180907_0826'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatquestion',
            name='shortcut',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
