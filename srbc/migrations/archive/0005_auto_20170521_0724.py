# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0004_auto_20170520_2005'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='diaryrecord',
            unique_together=set([('user', 'date')]),
        ),
    ]
