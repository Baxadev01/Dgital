# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-06 16:55


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0113_auto_20171228_0051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usernote',
            name='label',
            field=models.CharField(choices=[(b'DOC', '\u0414\u043e\u043a / \u041e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u044f'), (b'PZDC', '\u041a\u0440\u0438\u0437\u0438\u0441'), (b'IG', '\u0410\u043d\u0430\u043b\u0438\u0437 \u0418\u0413'), (b'CHAT', '\u041a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u0440\u0430\u0446\u0438\u043e\u043d\u0430'), (b'NB', '\u0421\u043b\u0443\u0436\u0435\u0431\u043d\u0430\u044f \u0437\u0430\u043c\u0435\u0442\u043a\u0430')], max_length=100),
        ),
    ]
