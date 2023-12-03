# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-01 15:55


from django.db import migrations, models
import shared.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0151_auto_20180330_0137'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_01',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_02',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_03',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_04',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_05',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_06',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_07',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_08',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_09',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_10',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_11',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_12',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_13',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_14',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_15',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurement_point_16',
            field=shared.models.DecimalRangeField(blank=True, decimal_places=3, max_digits=8, null=True),
        ),
    ]
