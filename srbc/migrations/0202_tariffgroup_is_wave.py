# Generated by Django 3.1 on 2020-11-03 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0200_auto_20201030_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='tariffgroup',
            name='is_wave',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
