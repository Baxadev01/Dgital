# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-16 06:10


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0038_auto_20170922_1105'),
    ]

    operations = [
        migrations.AddField(
            model_name='tgchat',
            name='is_main',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tgchat',
            name='next_chat',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='content.TGChat'),
        ),
    ]