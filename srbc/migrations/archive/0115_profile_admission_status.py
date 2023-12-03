# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-08 06:20


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0114_auto_20180106_1955'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='admission_status',
            field=models.CharField(blank=True, choices=[(b'NOT_STARTED', '\u041d\u0435 \u0434\u043e\u0448\u0435\u043b'), (b'IN_PROGRESS', '\u0412 \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u0435'), (b'DONE', '\u0417\u0430\u0432\u0435\u0440\u0448\u0438\u043b'), (b'PASSED', '\u041f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u043e, \u0432\u0441\u0451 \u043e\u043a'), (b'FAILED', '\u041f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u043e, \u0437\u0430\u0432\u0430\u043b\u0438\u043b')], default=b'NOT_STARTED', max_length=100),
        ),
    ]
