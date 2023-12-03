# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2020-01-22 03:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0036_auto_20190805_1433'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='campaign',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.Campaign'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='wave_channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='channel_campaigns', to='srbc.Wave'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='wave_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chat_campaigns', to='srbc.Wave'),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='applied_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='order',
            name='discount_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.DiscountCode'),
        ),
        migrations.AlterField(
            model_name='order',
            name='tariff',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='srbc.Tariff'),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='order',
            name='wave',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wave_to_join', to='srbc.Wave', verbose_name='Payment wave'),
        ),
        migrations.AlterField(
            model_name='renewalrequest',
            name='usernote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='srbc.UserNote'),
        ),
    ]
