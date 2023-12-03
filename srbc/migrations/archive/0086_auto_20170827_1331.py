# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-27 10:31


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0085_auto_20170827_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkpointrecord',
            name='front_image_hash',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='rear_image_hash',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='side_image_hash',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
    ]