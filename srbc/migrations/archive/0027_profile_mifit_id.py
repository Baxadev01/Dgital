# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0026_auto_20170611_0606'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='mifit_id',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
    ]
