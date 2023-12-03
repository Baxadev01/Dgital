# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-09-21 13:58


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0195_auto_20180921_1408'),
    ]

    operations = [
        migrations.CreateModel(
            name='TariffGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('communication_mode', models.CharField(blank=True, choices=[(b'CHANNEL', '\u041a\u0430\u043d\u0430\u043b'), (b'CHAT', '\u0427\u0430\u0442')], max_length=20, null=True)),
                ('analysis_queue', models.CharField(blank=True, choices=[(b'MANUAL', '\u0420\u0443\u0447\u043d\u043e\u0439 \u0437\u0430\u043f\u0440\u043e\u0441'), (b'AUTO', '\u0420\u0435\u0433\u0443\u043b\u044f\u0440\u043d\u044b\u0439 \u0430\u043d\u0430\u043b\u0438\u0437'), (b'NONE', '\u0411\u0435\u0437 \u0430\u043d\u0430\u043b\u0438\u0437\u0430')], max_length=20, null=True)),
                ('analysis_min_days', models.IntegerField(blank=True, default=0)),
                ('questions_per_day', models.IntegerField(blank=True, default=0)),
                ('meals_analyze', models.BooleanField(default=False)),
                ('checkpoints_required', models.CharField(choices=[(b'ALWAYS', '\u041a\u0430\u0436\u0434\u044b\u0435 2 \u043d\u0435\u0434\u0435\u043b\u0438'), (b'BMI', '\u041a\u0430\u0436\u0434\u044b\u0435 \u0434\u0432\u0435 \u043d\u0435\u0434\u0435\u043b\u0438 \u043f\u0440\u0438 \u0432\u044b\u0445\u043e\u0434\u0435 \u0437\u0430 \u043d\u043e\u0440\u043c\u0443 \u0418\u041c\u0422'), (b'NEVER', '\u041d\u0435\u0442 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0439')], max_length=20)),
                ('diary_data_required', models.IntegerField(blank=True, default=0)),
                ('diary_meals_required', models.IntegerField(blank=True, default=0)),
                ('meetings_access', models.CharField(choices=[(b'NONE', '\u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430'), (b'NEWBIE', '\u0414\u043e\u0441\u0442\u0443\u043f \u043a \u043d\u043e\u0432\u0438\u0447\u043a\u043e\u0432\u044b\u043c \u043c\u0438\u0442\u0438\u043d\u0433\u0430\u043c'), (b'ALL', '\u0414\u043e\u0441\u0442\u0443\u043f \u043a\u043e \u0432\u0441\u0435\u043c \u043c\u0438\u0442\u0438\u043d\u0433\u0430\u043c')], max_length=20)),
                ('kb_access', models.BooleanField(default=False)),
            ],
        ),
        migrations.RemoveField(
            model_name='tariffpermissions',
            name='action',
        ),
        migrations.RemoveField(
            model_name='tariffpermissions',
            name='tariff',
        ),
        migrations.RemoveField(
            model_name='tariff',
            name='communication_mode',
        ),
        migrations.DeleteModel(
            name='TariffAction',
        ),
        migrations.DeleteModel(
            name='TariffPermissions',
        ),
        migrations.AddField(
            model_name='tariff',
            name='tariff_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='srbc.TariffGroup'),
        ),
    ]
