# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-22 18:05


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0043_profile_paid_until'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='paid_until',
            new_name='valid_until',
        ),
    ]