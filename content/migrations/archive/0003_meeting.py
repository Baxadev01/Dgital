# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_basics'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('description', models.TextField()),
                ('is_uploaded', models.BooleanField(default=False)),
                ('is_playable', models.BooleanField(default=False)),
            ],
        ),
    ]
