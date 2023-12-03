# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0008_auto_20170521_1811'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_in_club',
            field=models.BooleanField(default=False),
        ),
    ]
