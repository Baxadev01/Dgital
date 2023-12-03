# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0016_auto_20170530_1053'),
    ]

    operations = [
        migrations.RenameField(
            model_name='diaryrecord',
            old_name='is_na',
            new_name='is_na_meals',
        ),
    ]
