# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-03 21:17


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0017_auto_20180404_0011'),
    ]

    operations = [
        migrations.AddField(
            model_name='renewalrequest',
            name='payment_special',
            field=models.BooleanField(default=False, verbose_name='\u041e\u0441\u043e\u0431\u044b\u0435 \u0443\u0441\u043b\u043e\u0432\u0438\u044f \u043e\u043f\u043b\u0430\u0442\u044b'),
        ),
    ]
