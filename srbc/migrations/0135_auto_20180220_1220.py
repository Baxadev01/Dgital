# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-20 09:20


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0007_auto_20180220_1220'),
        ('srbc', '0134_auto_20180219_1237'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='application',
            name='srbc_applic_is_trac_f0fd65_idx',
        ),
        migrations.RemoveIndex(
            model_name='application',
            name='srbc_applic_is_trac_0b5fca_idx',
        ),
        migrations.RemoveIndex(
            model_name='application',
            name='srbc_applic_is_trac_262a72_idx',
        ),
        migrations.RemoveField(
            model_name='application',
            name='is_tracker_payment_received',
        ),
        migrations.RemoveField(
            model_name='application',
            name='is_tracker_received',
        ),
        migrations.RemoveField(
            model_name='application',
            name='is_tracker_sent',
        ),
        migrations.AddField(
            model_name='application',
            name='active_payment_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='crm.Order'),
        ),
    ]
