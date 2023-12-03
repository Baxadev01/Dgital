# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-22 06:26


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0034_auto_20170826_1742'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dialogue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_created=True)),
                ('tg_user_id', models.IntegerField(blank=True, null=True)),
                ('text', models.TextField()),
                ('is_incoming', models.BooleanField()),
                ('tg_message_id', models.IntegerField(blank=True, null=True)),
                ('answered_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dialogue_answers', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dialogue_messages', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='dialogue',
            index=models.Index(fields=['created_at'], name='content_dia_created_312f89_idx'),
        ),
        migrations.AddIndex(
            model_name='dialogue',
            index=models.Index(fields=['answered_by'], name='content_dia_answere_87f152_idx'),
        ),
        migrations.AddIndex(
            model_name='dialogue',
            index=models.Index(fields=['user'], name='content_dia_user_id_6c72e0_idx'),
        ),
        migrations.AddIndex(
            model_name='dialogue',
            index=models.Index(fields=['tg_user_id'], name='content_dia_tg_user_e4454f_idx'),
        ),
        migrations.AddIndex(
            model_name='dialogue',
            index=models.Index(fields=['is_incoming'], name='content_dia_is_inco_3d38ff_idx'),
        ),
    ]