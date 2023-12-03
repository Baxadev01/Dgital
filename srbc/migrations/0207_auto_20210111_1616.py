# Generated by Django 3.1 on 2021-01-11 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0206_update_user_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='diaryrecord', name='last_sleep_updated', field=models.DateTimeField(
                blank=True, null=True, verbose_name='Последнее изменение данных о времени сна'),),
        migrations.AddField(
            model_name='diaryrecord', name='last_steps_updated', field=models.DateTimeField(
                blank=True, null=True, verbose_name='Последнее изменение данных о пройденных шагах'),),
        migrations.AddField(
            model_name='diaryrecord', name='last_weight_updated', field=models.DateTimeField(
                blank=True, null=True, verbose_name='Последнее изменение данных о весе'),),
        migrations.RunSQL(
            sql='''
                UPDATE public.srbc_diaryrecord
	            SET last_sleep_updated=last_data_updated, last_steps_updated=last_data_updated, last_weight_updated=last_data_updated
            ''',), ]