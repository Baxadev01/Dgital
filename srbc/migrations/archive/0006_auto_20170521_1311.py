# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0005_auto_20170521_0724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diaryrecord',
            name='sleep',
            field=models.DecimalField(null=True, max_digits=8, decimal_places=3, blank=True),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='trueweight',
            field=models.DecimalField(null=True, max_digits=8, decimal_places=3, blank=True),
        ),
        migrations.AlterField(
            model_name='diaryrecord',
            name='weight',
            field=models.DecimalField(null=True, max_digits=8, decimal_places=3, blank=True),
        ),
    ]
