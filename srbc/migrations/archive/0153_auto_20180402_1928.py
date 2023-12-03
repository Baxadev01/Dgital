# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-02 16:28


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0152_auto_20180402_1846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mealproduct',
            name='component_type',
            field=models.CharField(blank=True, choices=[(b'bread', '\u0425\u043b\u0435\u0431'), (b'fat', '\u0416\u0438\u0440\u043d\u044b\u0439 \u043f\u0440\u043e\u0434\u0443\u043a\u0442'), (b'carb', '\u0413\u043e\u0442\u043e\u0432\u044b\u0435 \u0443\u0433\u043b\u0435\u0432\u043e\u0434\u044b'), (b'rawcarb', '\u0421\u0443\u0445\u0438\u0435 \u0443\u0433\u043b\u0435\u0432\u043e\u0434\u044b'), (b'fatcarb', '\u0416\u0438\u0440\u043d\u044b\u0435 \u0443\u0433\u043b\u0435\u0432\u043e\u0434\u044b'), (b'protein', '\u0411\u0435\u043b\u043a\u043e\u0432\u044b\u0439 \u043f\u0440\u043e\u0434\u0443\u043a\u0442'), (b'deadweight', '\u0411\u0430\u043b\u043b\u0430\u0441\u0442'), (b'veg', '\u041e\u0432\u043e\u0449\u0438'), (b'fruit', '\u0424\u0440\u0443\u043a\u0442\u044b'), (b'dfruit', '\u0421\u0443\u0445\u043e\u0444\u0440\u0443\u043a\u0442\u044b'), (b'desert', '\u0414\u0435\u0441\u0435\u0440\u0442'), (b'drink', '\u041a\u0430\u043b\u043e\u0440\u0438\u0439\u043d\u044b\u0439 \u043d\u0430\u043f\u0438\u0442\u043e\u043a'), (b'alco', '\u0410\u043b\u043a\u043e\u0433\u043e\u043b\u044c')], default=None, max_length=50, null=True, verbose_name='\u041f\u0440\u043e\u0434\u0443\u043a\u0442'),
        ),
    ]
