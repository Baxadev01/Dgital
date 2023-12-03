# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-07-20 08:35


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0229_auto_20190720_1135'),
    ]

    operations = [
        migrations.RenameField(
            model_name='wave',
            old_name='is_archive',
            new_name='is_archived',
        ),
        migrations.AddIndex(
            model_name='wave',
            index=models.Index(fields=['is_archived'], name='srbc_wave_is_arch_1c6680_idx'),
        ),
    ]
