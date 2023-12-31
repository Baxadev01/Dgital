# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-10 12:17


from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0174_usernote_is_notification_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='gttresult',
            name='date_added',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gttresult',
            name='glucose_express',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='image_1',
            field=models.ImageField(blank=True, null=True, upload_to=srbc.models.gtt_image_upload_to_1),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='image_2',
            field=models.ImageField(blank=True, null=True, upload_to=srbc.models.gtt_image_upload_to_2),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='image_3',
            field=models.ImageField(blank=True, null=True, upload_to=srbc.models.gtt_image_upload_to_3),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='medical_comment',
            field=models.TextField(blank=True, null=True, verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u0432\u0440\u0430\u0447\u0430'),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='status',
            field=models.CharField(choices=[(b'NEW', '\u041d\u043e\u0432\u044b\u0439'), (b'DOC', '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043c\u0435\u0434\u0438\u0446\u0438\u043d\u0441\u043a\u043e\u0433\u043e \u0430\u043d\u0430\u043b\u0438\u0437\u0430'), (b'MEAL', '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0438 \u0440\u0430\u0446\u0438\u043e\u043d\u0430'), (b'DONE', '\u041f\u0440\u043e\u0430\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u043d')], default=b'NEW', max_length=50),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='user_note',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='srbc.UserNote'),
        ),
        migrations.AlterField(
            model_name='gttresult',
            name='medical_resolution',
            field=models.TextField(blank=True, null=True, verbose_name='\u0414\u0438\u0430\u0433\u043d\u043e\u0437'),
        ),
        migrations.AlterField(
            model_name='usernote',
            name='is_notification_sent',
            field=models.BooleanField(default=False, verbose_name='\u0423\u0432\u0435\u0434\u043e\u043c\u043b\u0451\u043d'),
        ),
    ]
