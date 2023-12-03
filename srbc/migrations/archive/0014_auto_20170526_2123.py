# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0013_auto_20170525_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord',
            name='is_mono',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_ooc',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_overcalory',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_unload',
            field=models.BooleanField(default=False),
        ),
    ]
