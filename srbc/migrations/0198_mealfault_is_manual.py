# Generated by Django 3.0.6 on 2020-10-23 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0197_auto_20201005_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='mealfault',
            name='is_manual',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]