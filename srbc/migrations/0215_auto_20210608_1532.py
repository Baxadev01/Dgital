# Generated by Django 3.1 on 2021-06-08 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0214_auto_20210322_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='tariffgroup',
            name='diary_access',
            field=models.CharField(choices=[('READ', 'Чтение'), ('WRITE', 'Запись'), ('ANLZ_AUTO', 'Автоматический анализ'), ('ANLZ_MANUAL', 'Ручной анализ')], default='READ', max_length=20),
        ),
    ]
