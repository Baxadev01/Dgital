# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-02 14:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0110_auto_20171202_1700'),
    ]

    operations = [
        migrations.AddField(
            model_name='autoanalizeformula',
            name='attention_required',
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name='autoanalizeformula',
            index=models.Index(fields=['attention_required'], name='srbc_autoan_attenti_c3204b_idx'),
        ),
    ]