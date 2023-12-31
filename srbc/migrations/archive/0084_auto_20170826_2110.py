# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-26 18:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0083_auto_20170819_2142'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='measurements_image',
        ),
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='weight_image',
        ),
        migrations.AlterField(
            model_name='checkpointrecord',
            name='front_image',
            field=models.ImageField(default=1, upload_to=b''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='checkpointrecord',
            name='rear_image',
            field=models.ImageField(default=1, upload_to=b''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='checkpointrecord',
            name='side_image',
            field=models.ImageField(default=1, upload_to=b''),
            preserve_default=False,
        ),
    ]
