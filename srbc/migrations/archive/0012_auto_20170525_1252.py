# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0011_auto_20170524_1707'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='techdutyshift',
            options={'ordering': ['-start_date']},
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='techduty',
            unique_together=set([('techcat', 'user', 'shift')]),
        ),
    ]
