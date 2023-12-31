# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-08-02 08:32


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0179_auto_20180802_1132'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiaryMealFault',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, default=b'')),
                ('diary_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='srbc.DiaryRecord', verbose_name='faults_list')),
                ('fault', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='srbc.MealFault')),
                ('meal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='srbc.DiaryMeal')),
                ('meal_component', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='srbc.MealComponent')),
            ],
        ),
    ]
