# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-15 18:58


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0205_auto_20181220_0636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='warning_flag',
            field=models.CharField(choices=[(b'TEST', '\u041d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u043e \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u043e\u0435 \u043e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0435'), (b'OBSERVATION', '\u0418\u043c\u0435\u044e\u0442\u0441\u044f \u043e\u0441\u043e\u0431\u0435\u043d\u043d\u043e\u0441\u0442\u0438 \u043e\u0431\u043c\u0435\u043d\u0430, \u0442\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u043d\u0430\u0431\u043b\u044e\u0434\u0435\u043d\u0438\u0435'), (b'TREATMENT', '\u041f\u043e\u0434 \u043d\u0430\u0431\u043b\u044e\u0434\u0435\u043d\u0438\u0435\u043c \u0432\u0440\u0430\u0447\u0435\u0439'), (b'DANGER', '\u041d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u043e \u043b\u0435\u0447\u0435\u043d\u0438\u0435, \u0442\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u043f\u043e\u0441\u0435\u0449\u0435\u043d\u0438\u0435 \u0432\u0440\u0430\u0447\u0430'), (b'PR', '\u041d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u043e \u043f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u043e\u0435 \u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u0435 \u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u043c \u0440\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0430\u0446\u0438\u044f\u043c'), (b'OOC', '\u041f\u0438\u0442\u0430\u043d\u0438\u0435 \u043d\u0435 \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0443\u0435\u0442 \u043c\u0435\u0442\u043e\u0434\u0438\u0447\u043a\u0435 \u0438 \u043e\u0431\u0449\u0438\u043c \u0440\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0430\u0446\u0438\u044f\u043c \u043f\u0440\u043e\u0435\u043a\u0442\u0430'), (b'OK', '\u0412\u0441\u0451 \u043e\u043a')], default=b'OK', max_length=20),
        ),
        migrations.AlterField(
            model_name='usernote',
            name='adjust_fruits',
            field=models.CharField(blank=True, choices=[(b'NO', '\u0411\u0435\u0437 \u0434\u043e\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0445 \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u0439'), (b'RESTRICT', '\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0438\u0442\u044c \u0444\u0440\u0443\u043a\u0442\u044b'), (b'EXCLUDE', '\u0417\u0430\u043c\u0435\u043d\u0438\u0442\u044c \u0444\u0440\u0443\u043a\u0442\u044b \u043d\u0430 \u043e\u0432\u043e\u0449\u0438 \u0438\u043b\u0438 \u043d\u0435\u0441\u043b\u0430\u0434\u043a\u0438\u0435 \u043a\u0440\u0435\u043a\u0435\u0440\u044b')], default=b'NO', max_length=20),
        ),
    ]
