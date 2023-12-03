# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0029_auto_20170614_2217'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SRBCGroup',
            new_name='Wave',
        ),
        migrations.RenameField(
            model_name='profile',
            old_name='srbc_group',
            new_name='wave',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='invite',
        ),
        migrations.AddField(
            model_name='invitation',
            name='applied_by',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='invitation',
            name='wave',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, blank=True, to='srbc.Wave', null=True),
        ),
    ]
