# -*- coding: utf-8 -*-


from django.db import migrations, models
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0015_diaryrecord_is_na'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diaryrecord',
            name='faults',
            field=srbc.models.IntegerRangeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='meals',
            field=srbc.models.IntegerRangeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='sleep',
            field=srbc.models.DecimalRangeField(null=True, max_digits=8, decimal_places=3, blank=True),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='steps',
            field=srbc.models.IntegerRangeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='trueweight',
            field=srbc.models.DecimalRangeField(null=True, max_digits=8, decimal_places=3, blank=True),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='weight',
            field=srbc.models.DecimalRangeField(null=True, max_digits=8, decimal_places=3, blank=True),
        ),
    ]
