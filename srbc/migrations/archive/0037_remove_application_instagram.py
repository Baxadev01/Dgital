# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0036_auto_20170617_1647'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='application',
            name='instagram',
        ),
    ]
