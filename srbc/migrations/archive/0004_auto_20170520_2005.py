# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0003_auto_20170520_1704'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diaryrecord',
            name='trueweight',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=3, blank=True),
        ),
    ]
