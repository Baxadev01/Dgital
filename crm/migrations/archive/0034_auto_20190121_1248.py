# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-21 09:48


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0033_application_goal_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='baby_birthdate',
            field=models.DateField(blank=True, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u0440\u0435\u0431\u0451\u043d\u043a\u0430'),
        ),
        migrations.AddField(
            model_name='application',
            name='baby_case',
            field=models.CharField(blank=True, choices=[(b'PREGNANT', '\u0411\u0435\u0440\u0435\u043c\u0435\u043d\u043d\u043e\u0441\u0442\u044c'), (b'FEEDING', '\u041a\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u0435 \u0433\u0440\u0443\u0434\u044c\u044e'), (b'NONE', '\u041d\u0438\u0447\u0435\u0433\u043e \u0438\u0437 \u043f\u0435\u0440\u0435\u0447\u0438\u0441\u043b\u0435\u043d\u043d\u043e\u0433\u043e')], default=b'NONE', max_length=100, verbose_name='\u041e\u0441\u043e\u0431\u044b\u0439 \u0441\u043b\u0443\u0447\u0430\u0439'),
        ),
    ]
