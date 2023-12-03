# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-15 17:02


import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crm', '0004_campaign_is_admission_open'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_provider', models.CharField(choices=[(b'YA', '\u042f\u043d\u0434\u0435\u043a\u0441-\u041a\u0430\u0441\u0441\u0430'), (b'PP', 'PayPal'), (b'MANUAL', '\u0412\u0440\u0443\u0447\u043d\u0443\u044e')], max_length=100)),
                ('payment_id', models.IntegerField(blank=True, null=True)),
                ('date_added', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('status', models.CharField(choices=[(b'PENDING', '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043e\u043f\u043b\u0430\u0442\u044b'), (b'APPROVED', '\u041e\u043f\u043b\u0430\u0447\u0435\u043d'), (b'CANCELED', '\u041e\u0442\u043c\u0435\u043d\u0435\u043d')], max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u0417\u0430\u043a\u0430\u0437',
                'verbose_name_plural': '\u0417\u0430\u043a\u0430\u0437\u044b',
            },
        ),
    ]