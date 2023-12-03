# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-03 20:57


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crm', '0015_auto_20180330_0137'),
    ]

    operations = [
        migrations.CreateModel(
            name='RenewalRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_type', models.CharField(choices=[(b'POSITIVE', '#\u044f\u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u044e'), (b'NEGATIVE', '#\u044f\u041d\u0415\u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u044e')], max_length=10, verbose_name='\u0425\u044d\u0448\u0442\u0435\u0433')),
                ('comment', models.TextField(verbose_name='\u041e\u0442\u0437\u044b\u0432')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(blank=True, choices=[(b'NEW', '\u041d\u043e\u0432\u044b\u0439'), (b'PREACCEPTED', '\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u043e \u043e\u0434\u043e\u0431\u0440\u0435\u043d'), (b'TBD', '\u0422\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u0441\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0438\u0435'), (b'REJECTED', '\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d'), (b'ACCEPTED', '\u041e\u0434\u043e\u0431\u0440\u0435\u043d')], default=b'NEW', max_length=25)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
