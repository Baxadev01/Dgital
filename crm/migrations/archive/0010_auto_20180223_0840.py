# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-23 05:40


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0009_order_wave'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[(b'PENDING', '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043e\u043f\u043b\u0430\u0442\u044b'), (b'PROCESSING', '\u0412 \u043e\u0431\u0440\u0430\u0431\u043e\u0442\u043a\u0435'), (b'APPROVED', '\u041e\u043f\u043b\u0430\u0447\u0435\u043d'), (b'CANCELED', '\u041e\u0442\u043c\u0435\u043d\u0435\u043d')], default=b'PENDING', max_length=100),
        ),
    ]
