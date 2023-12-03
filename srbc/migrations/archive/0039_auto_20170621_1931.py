# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-21 19:31


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0038_profile_trueweight_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='is_tracker_payment_received',
            field=models.BooleanField(default=False, verbose_name='\u041f\u043e\u043b\u0443\u0447\u0435\u043d\u0430 \u043e\u043f\u043b\u0430\u0442\u0430 \u0437\u0430 \u0442\u0440\u0435\u043a\u0435\u0440'),
        ),
        migrations.AddField(
            model_name='application',
            name='is_tracker_received',
            field=models.BooleanField(default=False, verbose_name='\u0422\u0440\u0435\u043a\u0435\u0440 \u043f\u043e\u043b\u0443\u0447\u0435\u043d'),
        ),
        migrations.AddField(
            model_name='application',
            name='is_tracker_sent',
            field=models.BooleanField(default=False, verbose_name='\u0422\u0440\u0435\u043a\u0435\u0440 \u0432\u044b\u0441\u043b\u0430\u043d'),
        ),
    ]