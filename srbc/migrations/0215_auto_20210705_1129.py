# Generated by Django 3.1 on 2021-07-05 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0214_auto_20210322_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord',
            name='pers_rec_check_mode',
            field=models.CharField(choices=[('AUTO', 'Автоматический'), ('MANUAL', 'Ручной')], default='AUTO', max_length=20, verbose_name='Режим проверки'),
        ),
    ]
