# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-20 06:07


from django.db import migrations, models
import django.db.models.deletion
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0120_auto_20180118_1653'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=25)),
                ('start_date', models.DateField()),
                ('mailchimp_group_id', models.CharField(blank=True, max_length=25, null=True)),
                ('is_active', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='rejection_reason',
        ),
        migrations.AddField(
            model_name='application',
            name='email_status',
            field=models.CharField(blank=True, choices=[(b'NEW', '\u041d\u043e\u0432\u044b\u0439'), (b'PENDING', '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f'), (b'APPROVED', '\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d'), (b'DISCONNECTED', '\u041e\u0442\u043f\u0438\u0441\u0430\u043d')], default=b'NEW', max_length=25),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='rejection_comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='checkpointrecord',
            name='rejection_reasons',
            field=srbc.models.ChoiceArrayField(base_field=models.CharField(choices=[(b'CLOTHES', b'\xd0\x9d\xd0\xb5\xd1\x83\xd0\xb4\xd0\xb0\xd1\x87\xd0\xbd\xd0\xb0\xd1\x8f \xd0\xbe\xd0\xb4\xd0\xb5\xd0\xb6\xd0\xb4\xd0\xb0 (\xd0\xbb\xd0\xb5\xd0\xb3\xd0\xb3\xd0\xb8\xd0\xbd\xd1\x81\xd1\x8b, \xd1\x84\xd1\x83\xd1\x82\xd0\xb1\xd0\xbe\xd0\xbb\xd0\xba\xd0\xb8, \xd1\x81\xd0\xbb\xd0\xb8\xd1\x82\xd0\xbd\xd1\x8b\xd0\xb9 \xd0\xba\xd1\x83\xd0\xbf\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xb8\xd0\xba \xd0\xb8 \xd1\x82.\xd0\xb4.)'), (b'CUTOFF', b'\xd0\x9e\xd0\xb1\xd1\x80\xd0\xb5\xd0\xb7\xd0\xb0\xd0\xbd\xd1\x8b \xd1\x87\xd0\xb0\xd1\x81\xd1\x82\xd0\xb8 \xd1\x82\xd0\xb5\xd0\xbb\xd0\xb0 (\xd0\xbd\xd0\xb5\xd1\x82 \xd0\xbd\xd0\xbe\xd0\xb3-\xd0\xb3\xd0\xbe\xd0\xbb\xd0\xbe\xd0\xb2\xd1\x8b)'), (b'ANGLE', b'\xd0\x9d\xd0\xb5\xd0\xbf\xd1\x80\xd0\xb0\xd0\xb2\xd0\xb8\xd0\xbb\xd1\x8c\xd0\xbd\xd1\x8b\xd0\xb9 \xd1\x80\xd0\xb0\xd0\xba\xd1\x83\xd1\x80\xd1\x81 (\xd1\x81\xd0\xb2\xd0\xb5\xd1\x80\xd1\x85\xd1\x83 \xd0\xb2\xd0\xbd\xd0\xb8\xd0\xb7 \xd0\xb8\xd0\xbb\xd0\xb8 \xd1\x81\xd0\xbd\xd0\xb8\xd0\xb7\xd1\x83 \xd0\xb2\xd0\xb2\xd0\xb5\xd1\x80\xd1\x85)'), (b'POSE', b'\xd0\x9d\xd0\xb5\xd0\xbf\xd1\x80\xd0\xb0\xd0\xb2\xd0\xb8\xd0\xbb\xd1\x8c\xd0\xbd\xd1\x8b\xd0\xb0\xd1\x8f \xd0\xbf\xd0\xbe\xd0\xb7\xd0\xb0 (\xd1\x82\xd1\x80\xd0\xb8 \xd1\x87\xd0\xb5\xd1\x82\xd0\xb2\xd0\xb5\xd1\x80\xd1\x82\xd0\xb8 \xd0\xb2\xd0\xbc\xd0\xb5\xd1\x81\xd1\x82\xd0\xbe \xd0\xb0\xd0\xbd\xd1\x84\xd0\xb0\xd1\x81 \xd0\xb8 \xd1\x82.\xd0\xbf., \xd1\x80\xd1\x83\xd0\xba\xd0\xb8 \xd0\xb7\xd0\xb0\xd0\xba\xd1\x80\xd1\x8b\xd0\xb2\xd0\xb0\xd1\x8e\xd1\x82 \xd0\xb8\xd0\xb7\xd0\xb3\xd0\xb8\xd0\xb1 \xd1\x81\xd0\xbf\xd0\xb8\xd0\xbd\xd1\x8b)'), (b'LIGHT', b'\xd0\x9d\xd0\xb5\xd0\xb4\xd0\xbe\xd1\x81\xd1\x82\xd0\xb0\xd1\x82\xd0\xbe\xd1\x87\xd0\xbd\xd0\xb0\xd1\x8f \xd0\xbe\xd1\x81\xd0\xb2\xd0\xb5\xd1\x89\xd0\xb5\xd0\xbd\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c-\xd0\xba\xd0\xbe\xd0\xbd\xd1\x82\xd1\x80\xd0\xb0\xd1\x81\xd1\x82\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c (\xd1\x81\xd0\xbd\xd1\x8f\xd1\x82\xd0\xbe \xd0\xb2 \xd1\x82\xd0\xb5\xd0\xbc\xd0\xbd\xd0\xbe\xd1\x82\xd0\xb5, \xd1\x81\xd0\xbd\xd1\x8f\xd1\x82\xd0\xbe \xd0\xbf\xd1\x80\xd0\xbe\xd1\x82\xd0\xb8\xd0\xb2 \xd1\x81\xd0\xb2\xd0\xb5\xd1\x82\xd0\xb0)'), (b'BACKGROUND', b'\xd0\x9d\xd0\xb5\xd0\xbf\xd1\x80\xd0\xb0\xd0\xb2\xd0\xb8\xd0\xbb\xd1\x8c\xd0\xbd\xd1\x8b\xd0\xb9 \xd1\x84\xd0\xbe\xd0\xbd (\xd0\xbe\xd1\x87\xd0\xb5\xd0\xbd\xd1\x8c \xd0\xbf\xd0\xb5\xd1\x81\xd1\x82\xd1\x80\xd1\x8b\xd0\xb9)'), (b'BLUR', b'\xd0\xa4\xd0\xbe\xd1\x82\xd0\xbe\xd0\xb3\xd1\x80\xd0\xb0\xd1\x84\xd0\xb8\xd0\xb8 \xd0\xbd\xd0\xb5 \xd0\xb2 \xd1\x84\xd0\xbe\xd0\xba\xd1\x83\xd1\x81\xd0\xb5 (\xd0\xb8\xd0\xb7\xd0\xbe\xd0\xb1\xd1\x80\xd0\xb0\xd0\xb6\xd0\xb5\xd0\xbd\xd0\xb8\xd0\xb5 \xd1\x80\xd0\xb0\xd0\xb7\xd0\xbc\xd1\x8b\xd1\x82\xd0\xbe)')], max_length=50), blank=True, default=[], size=None),
        ),
        migrations.AddField(
            model_name='application',
            name='campaign',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='srbc.Campaign'),
        ),
    ]
