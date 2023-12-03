# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0035_auto_20170617_1258'),
    ]

    operations = [
        migrations.RenameField(
            model_name='application',
            old_name='is_locked',
            new_name='is_approved',
        ),
    ]
