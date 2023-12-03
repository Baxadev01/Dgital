# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-13 02:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0054_auto_20180111_1340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useradmissiontest',
            name='recommendation_info',
            field=models.TextField(blank=True, null=True, verbose_name='\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043e \u0440\u0435\u043a\u043e\u043c\u043c\u0435\u043d\u0434\u0430\u0442\u0435\u043b\u0435'),
        ),
        migrations.AlterField(
            model_name='useradmissiontest',
            name='status',
            field=models.CharField(blank=True, choices=[(b'NOT_STARTED', '\u041d\u0435 \u0434\u043e\u0448\u0435\u043b'), (b'IN_PROGRESS', '\u0412 \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u0435'), (b'DONE', '\u0417\u0430\u0432\u0435\u0440\u0448\u0438\u043b'), (b'PASSED', '\u041f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u043e, \u0432\u0441\u0451 \u043e\u043a'), (b'FAILED', '\u041f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u043e, \u0437\u0430\u0432\u0430\u043b\u0438\u043b'), (b'REJECTED', '\u041e\u0442\u043a\u0430\u0437\u0430\u043d\u043e'), (b'ACCEPTED', '\u041f\u0440\u0438\u043d\u044f\u0442')], default=b'NOT_STARTED', max_length=100),
        ),
    ]
