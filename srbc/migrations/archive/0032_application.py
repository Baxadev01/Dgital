# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0031_invitation_club_only'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gender', models.CharField(max_length=1, choices=[(b'M', '\u041c\u0443\u0436\u0441\u043a\u043e\u0439'), (b'F', '\u0416\u0435\u043d\u0441\u043a\u0438\u0439')])),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('height', models.IntegerField()),
                ('weight', srbc.models.DecimalRangeField(null=True, max_digits=8, decimal_places=3, blank=True)),
                ('age', models.IntegerField()),
                ('sickness', models.TextField()),
                ('goals', models.TextField()),
                ('instagram', models.CharField(max_length=100)),
                ('have_tracker', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='application', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
