# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-13 11:33


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0176_auto_20180710_1850'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gttresult',
            name='user_note',
        ),
        migrations.AddField(
            model_name='gttresult',
            name='meal_comment',
            field=models.TextField(blank=True, null=True, verbose_name='\u041a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u0440\u0430\u0446\u0438\u043e\u043d\u0430'),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='user_note_doc',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gtt_doc', to='srbc.UserNote'),
        ),
        migrations.AddField(
            model_name='gttresult',
            name='user_note_meal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gtt_meal', to='srbc.UserNote'),
        ),
    ]
