# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0014_auto_20170526_2123'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord',
            name='is_na',
            field=models.BooleanField(default=False),
        ),
    ]
