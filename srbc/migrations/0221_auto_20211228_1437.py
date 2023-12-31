# Generated by Django 3.1.7 on 2021-12-28 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0219_auto_20211020_1540'),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonalRecommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AlterField(
            model_name='usernote',
            name='adjust_fruits',
            field=models.CharField(blank=True, choices=[('NO', 'Без дополнительных ограничений'), ('RESTRICT', 'Минимизация моно- и дисахаридов'), ('EXCLUDE', 'Замена моно- и дисахаридов')], default='NO', max_length=20),
        ),
    ]
