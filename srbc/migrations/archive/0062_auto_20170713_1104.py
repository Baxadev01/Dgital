# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-13 11:04


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0061_auto_20170713_1104'),
    ]

    operations = [
        migrations.RenameField(
            model_name='instagramimage',
            old_name='date',
            new_name='post_date',
        ),
    ]