# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-14 11:27


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0163_auto_20180414_0926'),
    ]

    operations = [
        migrations.RenameField(
            model_name='checkpointphotos',
            old_name='front_image_cropped',
            new_name='cropped_front_image',
        ),
    ]
