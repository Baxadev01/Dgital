# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-13 22:05


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0130_remove_profile_admission_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='GTTResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('glucose_0', models.FloatField(blank=True, null=True)),
                ('glucose_60', models.FloatField(blank=True, null=True)),
                ('glucose_120', models.FloatField(blank=True, null=True)),
                ('insulin_0', models.FloatField(blank=True, null=True)),
                ('insulin_60', models.FloatField(blank=True, null=True)),
                ('insulin_120', models.FloatField(blank=True, null=True)),
                ('homa_index', models.FloatField(blank=True, null=True)),
                ('medical_resolution', models.TextField(blank=True, null=True)),
                ('is_reviewed', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gtt_results', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
