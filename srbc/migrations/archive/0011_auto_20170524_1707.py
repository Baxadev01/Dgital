# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0010_auto_20170522_1406'),
    ]

    operations = [
        migrations.CreateModel(
            name='TechDuty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mode', models.CharField(default=b'AUTO', max_length=100, choices=[(b'AUTO', '\u0414\u0435\u0436\u0443\u0440\u043d\u044b\u0439'), (b'MANUAL', '\u0414\u043e\u0431\u0440\u043e\u0432\u043e\u043b\u0435\u0446')])),
            ],
        ),
        migrations.CreateModel(
            name='TechDutyShift',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='techcat',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='CatOnDuty', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='techduty',
            name='shift',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='srbc.TechDutyShift'),
        ),
        migrations.AddField(
            model_name='techduty',
            name='techcat',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='techduty',
            name='user',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='SupervisedUser', to=settings.AUTH_USER_MODEL),
        ),
    ]
