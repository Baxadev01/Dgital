# Generated by Django 3.1.7 on 2022-02-20 20:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0224_auto_20220208_1047'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiaryRecordAnalysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('containers', models.JSONField(blank=True, default=list, null=True)),
                ('day_stat', models.JSONField(blank=True, default=list, null=True)),
                ('diary', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis', to='srbc.diaryrecord')),
            ],
        ),
    ]
