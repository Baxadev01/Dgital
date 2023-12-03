# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0019_auto_20170603_0820'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserBookMark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bookmarked_user', models.ForeignKey(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE,related_name='bookmarks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='usernote',
            name='date_added',
            field=models.DateTimeField(default=datetime.datetime.now, blank=True),
        ),
    ]
