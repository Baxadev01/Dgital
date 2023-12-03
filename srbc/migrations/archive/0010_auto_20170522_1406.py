# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0009_profile_is_in_club'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instagramimage',
            name='role',
            field=models.CharField(max_length=100, choices=[(b'FOOD', '\u0415\u0414\u0410'), (b'PHOTO', '\u0424\u041e\u0422\u041e'), (b'DATA', '\u0414\u0410\u041d\u041d\u042b\u0415'), (b'MEASURE', '\u0417\u0410\u041c\u0415\u0420\u042b'), (b'UNKNOWN', 'N/A'), (b'GOAL', '\u0426\u0415\u041b\u0418')]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='gender',
            field=models.CharField(default=b'F', max_length=1, choices=[(b'M', '\u041c\u0443\u0436\u0441\u043a\u043e\u0439'), (b'F', '\u0416\u0435\u043d\u0441\u043a\u0438\u0439')]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='sugar_status',
            field=models.IntegerField(default=0, choices=[(0, '\u0412 \u043d\u043e\u0440\u043c\u0435'), (1, '\u0418\u043d\u0441\u0443\u043b\u0438\u043d\u043e\u0440\u0435\u0437\u0438\u0441\u0442\u0435\u043d\u0442\u043d\u043e\u0441\u0442\u044c'), (2, '\u0413\u043b\u044e\u043a\u043e\u0437\u043e\u0442\u043e\u043b\u0435\u0440\u0430\u043d\u0442\u043d\u043e\u0441\u0442\u044c'), (3, '\u0414\u0438\u0430\u0431\u0435\u0442'), (99, '\u041d\u0435 \u043e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u043e')]),
        ),
    ]
