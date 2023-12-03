# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0024_profile_group_leader'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='data_sergeant',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='data_users', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='meals_sergeant',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='meal_users', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
