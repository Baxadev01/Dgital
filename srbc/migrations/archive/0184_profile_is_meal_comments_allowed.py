# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-08-09 17:31


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0183_auto_20180806_1857'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_meal_comments_allowed',
            field=models.BooleanField(default=True, verbose_name='\u0420\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u044b \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438 \u043a \u0440\u0430\u0446\u0438\u043e\u043d\u0443'),
        ),
    ]
