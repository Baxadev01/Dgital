# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-14 06:13


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0065_auto_20170713_1901'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='visibility',
            field=models.CharField(choices=[(b'PUBLIC', '\u041e\u0442\u043a\u0440\u044b\u0442\u044b\u0439'), (b'RESTRICTED', '\u041c\u0430\u0440\u0430\u0444\u043e\u043d\u0441\u043a\u0438\u0439'), (b'PRIVATE', '\u0417\u0430\u043a\u0440\u044b\u0442\u044b\u0439')], default=b'PRIVATE', max_length=20),
        ),
    ]
