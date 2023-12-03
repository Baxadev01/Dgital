# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=225)),
                ('body', models.TextField()),
                ('comment', models.TextField(default=b'', blank=True)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), size=None)),
            ],
        ),
    ]
