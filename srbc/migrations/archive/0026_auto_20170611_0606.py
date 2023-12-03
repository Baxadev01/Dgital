# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0025_auto_20170610_0605'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='data_sergeant',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='data_users', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='group_leader',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='squadron', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='meals_sergeant',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='meal_users', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
