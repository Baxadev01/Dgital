# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-03-28 21:46


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0149_auto_20180329_0043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diaryrecord',
            name='data_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diary_record', to='srbc.InstagramImage'),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='meal_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='diary_record', to='srbc.SRBCImage'),
        ),
    ]