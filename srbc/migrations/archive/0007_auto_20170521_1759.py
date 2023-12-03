# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.contrib.postgres.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('social_django', '0006_partial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0006_auto_20170521_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstagramImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('real_date', models.DateField(null=True, blank=True)),
                ('image_id', models.CharField(max_length=255)),
                ('image', models.ImageField(upload_to=b'')),
                ('post_text', models.TextField()),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), size=None)),
                ('image_class', models.CharField(max_length=100, choices=[(b'FOOD', 'Food'), (b'PHOTO', 'Photo'), (b'CPHOTO', 'Checkpoint Photo'), (b'DATA', 'Data'), (b'MEASURE', 'Measurements'), (b'GOAL', 'Goals')])),
                ('instagram_account', models.ForeignKey(on_delete=models.deletion.CASCADE, to='social_django.UserSocialAuth')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_locked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_perfect_weight',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_pregnant',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_sick',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='is_validated',
            field=models.BooleanField(default=False),
        ),
    ]
