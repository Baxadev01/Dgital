# -*- coding: utf-8 -*-


from django.db import migrations, models
import srbc.models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0032_application'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='application',
            name='have_tracker',
        ),
        migrations.AddField(
            model_name='application',
            name='need_tracker',
            field=models.BooleanField(default=False, verbose_name='\u0425\u043e\u0447\u0443 \u0444\u0438\u0442\u043d\u0435\u0441\u0441-\u0442\u0440\u0435\u043a\u0435\u0440'),
        ),
        migrations.AlterField(
            model_name='application',
            name='age',
            field=models.IntegerField(verbose_name='\u0412\u0430\u0448 \u0432\u043e\u0437\u0440\u0430\u0441\u0442'),
        ),
        migrations.AlterField(
            model_name='application',
            name='city',
            field=models.CharField(max_length=100, verbose_name='\u0413\u043e\u0440\u043e\u0434'),
        ),
        migrations.AlterField(
            model_name='application',
            name='country',
            field=models.CharField(max_length=100, verbose_name='\u0421\u0442\u0440\u0430\u043d\u0430'),
        ),
        migrations.AlterField(
            model_name='application',
            name='email',
            field=models.EmailField(max_length=254, verbose_name='\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u0430\u044f \u043f\u043e\u0447\u0442\u0430'),
        ),
        migrations.AlterField(
            model_name='application',
            name='first_name',
            field=models.CharField(max_length=100, verbose_name='\u0418\u043c\u044f'),
        ),
        migrations.AlterField(
            model_name='application',
            name='gender',
            field=models.CharField(default=b'F', max_length=1, verbose_name='\u041f\u043e\u043b', choices=[(b'M', '\u041c\u0443\u0436\u0441\u043a\u043e\u0439'), (b'F', '\u0416\u0435\u043d\u0441\u043a\u0438\u0439')]),
        ),
        migrations.AlterField(
            model_name='application',
            name='goals',
            field=models.TextField(verbose_name='\u0426\u0435\u043b\u0438 \u043d\u0430 \u043c\u0430\u0440\u0430\u0444\u043e\u043d'),
        ),
        migrations.AlterField(
            model_name='application',
            name='height',
            field=models.IntegerField(verbose_name='\u0412\u0430\u0448 \u0440\u043e\u0441\u0442'),
        ),
        migrations.AlterField(
            model_name='application',
            name='instagram',
            field=models.CharField(max_length=100, verbose_name='\u041c\u0430\u0440\u0430\u0444\u043e\u043d\u0441\u043a\u0438\u0439 Instagram-\u0430\u043a\u043a\u0430\u0443\u043d\u0442'),
        ),
        migrations.AlterField(
            model_name='application',
            name='last_name',
            field=models.CharField(max_length=100, verbose_name='\u0424\u0430\u043c\u0438\u043b\u0438\u044f'),
        ),
        migrations.AlterField(
            model_name='application',
            name='phone',
            field=models.CharField(max_length=100, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u043c\u043e\u0431\u0438\u043b\u044c\u043d\u043e\u0433\u043e \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430'),
        ),
        migrations.AlterField(
            model_name='application',
            name='sickness',
            field=models.TextField(verbose_name='\u0418\u043c\u0435\u044e\u0449\u0438\u0435\u0441\u044f \u0437\u0430\u0431\u043e\u043b\u0435\u0432\u0430\u043d\u0438\u044f'),
        ),
        migrations.AlterField(
            model_name='application',
            name='weight',
            field=srbc.models.DecimalRangeField(null=True, verbose_name='\u0412\u0430\u0448 \u0442\u0435\u043a\u0443\u0449\u0438\u0439 (\u0441\u0442\u0430\u0440\u0442\u043e\u0432\u044b\u0439) \u0432\u0435\u0441', max_digits=8, decimal_places=3, blank=True),
        ),
    ]
