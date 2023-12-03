# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0030_auto_20170616_1437'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='club_only',
            field=models.BooleanField(default=False),
        ),
    ]
