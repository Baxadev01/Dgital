# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0017_auto_20170603_0539'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord',
            name='is_na_data',
            field=models.BooleanField(default=False),
        ),
    ]
