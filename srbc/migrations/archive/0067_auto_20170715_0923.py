# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-15 09:23


from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0066_profile_visibility'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usernote',
            name='content',
            field=markdownx.models.MarkdownxField(blank=True, default=b''),
        ),
    ]
