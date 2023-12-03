# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-13 19:01


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0064_auto_20170713_1528'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='instagramimage',
            index=models.Index(fields=['user'], name='srbc_instag_user_id_7be1a4_idx'),
        ),
        migrations.AddIndex(
            model_name='instagramimage',
            index=models.Index(fields=['post_date'], name='srbc_instag_post_da_0e8dec_idx'),
        ),
        migrations.AddIndex(
            model_name='instagramimage',
            index=models.Index(fields=['role'], name='srbc_instag_role_d9a184_idx'),
        ),
    ]
