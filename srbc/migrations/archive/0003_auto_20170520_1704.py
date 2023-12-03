# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0002_auto_20170520_0943'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='diaryrecord',
            options={'ordering': ['date']},
        ),
        migrations.AlterModelOptions(
            name='srbcgroup',
            options={'ordering': ['-start_date']},
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='sleep',
            field=models.DecimalField(null=True, max_digits=4, decimal_places=2, blank=True),
        ),
    ]
