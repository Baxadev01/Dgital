# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-28 23:57


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0041_remove_tgpost_wave'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tgchat',
            name='next_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='content.TGChat'),
        ),
    ]
