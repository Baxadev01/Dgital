# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0034_application_is_locked'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='is_locked',
            field=models.BooleanField(default=False, verbose_name='\u041f\u0440\u043e\u0444\u0438\u043b\u044c \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d'),
        ),
        migrations.AlterField(
            model_name='application',
            name='phone',
            field=models.CharField(max_length=100, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u043c\u043e\u0431\u0438\u043b\u044c\u043d\u043e\u0433\u043e \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430', blank=True),
        ),
    ]
