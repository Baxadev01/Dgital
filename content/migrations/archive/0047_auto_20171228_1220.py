# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-12-28 09:20


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0046_auto_20171228_0350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatquestion',
            name='answered_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_questions_replies_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
