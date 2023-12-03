# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0033_auto_20170617_0839'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='is_locked',
            field=models.BooleanField(default=False, verbose_name='\u041f\u0440\u043e\u0432\u0438\u043b\u044c \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d'),
        ),
    ]
