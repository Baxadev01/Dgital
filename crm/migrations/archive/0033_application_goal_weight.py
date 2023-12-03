# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-21 09:02


from django.db import migrations
import shared.models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0032_remove_campaign_is_open'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='goal_weight',
            field=shared.models.DecimalRangeField(decimal_places=3, max_digits=8, null=True, verbose_name='\u0426\u0435\u043b\u0435\u0432\u043e\u0439 \u0432\u0435\u0441'),
        ),
    ]
