# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-06 17:26


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0072_auto_20170723_1841'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diaryrecord',
            name='faults_data',
        ),
    ]
