# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-20 16:29


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0025_tgchat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tgchat',
            name='chat_type',
            field=models.CharField(blank=True, choices=[(b'CHAT', b'Chat'), (b'CHANNEL', b'Channel')], default=b'CHAT', max_length=20),
        ),
        migrations.AlterField(
            model_name='tgchat',
            name='title',
            field=models.CharField(max_length=100),
        ),
    ]
