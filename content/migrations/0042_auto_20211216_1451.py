# Generated by Django 3.1.7 on 2021-12-16 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0041_add_tg_translations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dialogue',
            name='tg_user_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
