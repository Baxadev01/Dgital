# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-20 19:01


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0031_remove_campaign_is_admission_open'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaign',
            name='is_open',
        ),
    ]