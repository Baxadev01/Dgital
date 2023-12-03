# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0023_auto_20170608_0615'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='group_leader',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='squadron', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
