# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0012_auto_20170525_1252'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='diaryrecord',
            index_together=set([('user', 'date')]),
        ),
    ]
