# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-07-31 10:42


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0243_auto_20190730_1319'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='meal_analyze_mode',
            field=models.SmallIntegerField(blank=True, choices=[(0, '\u0421\u0430\u043c\u043e\u043e\u0446\u0438\u0444\u0440\u043e\u0432\u043a\u0430'), (1, '\u041f\u043e\u0434\u0440\u043e\u0431\u043d\u044b\u0435 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438'), (2, '\u041a\u0440\u0430\u0442\u043a\u0438\u0435 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438'), (3, '\u0411\u0435\u0437 \u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0435\u0432')], default=1),
        ),
    ]
