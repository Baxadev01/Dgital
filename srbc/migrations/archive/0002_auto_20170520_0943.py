# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SRBCGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=25)),
                ('start_date', models.DateField()),
                ('is_in_club', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='profile',
            name='srbc_group',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, blank=True, to='srbc.SRBCGroup', null=True),
        ),
    ]
