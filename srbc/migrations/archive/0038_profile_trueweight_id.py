# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0037_remove_application_instagram'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='trueweight_id',
            field=models.CharField(max_length=11, null=True, blank=True),
        ),
    ]
