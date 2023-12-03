# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Basics',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('keyword', models.CharField(max_length=100)),
                ('body', models.TextField()),
                ('type', models.CharField(default=b'TEXT', max_length=20, choices=[(b'TEXT', '\u0422\u0435\u043a\u0441\u0442'), (b'IMAGE', '\u0418\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435')])),
            ],
        ),
    ]
