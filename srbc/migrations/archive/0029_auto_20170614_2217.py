# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0028_auto_20170612_1631'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=100)),
                ('expiring_at', models.DateTimeField(null=True, blank=True)),
                ('is_applied', models.BooleanField(default=False)),
                ('applied_at', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_id',
            field=models.CharField(max_length=100, unique=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='telegram_join_code',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='instagram',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='invite',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, blank=True, to='srbc.Invitation', null=True),
        ),
    ]
