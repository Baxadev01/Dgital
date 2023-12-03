# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0021_auto_20170608_0613'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='sugar_status',
            new_name='warning_flag',
        ),
    ]
