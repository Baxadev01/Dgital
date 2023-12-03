# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0022_auto_20170608_0614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='warning_flag',
            field=models.CharField(default=b'TEST', max_length=20, choices=[(b'TEST', '\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u044b \u0430\u043d\u0430\u043b\u0438\u0437\u044b'), (b'OBSERVATION', '\u0412 \u0437\u043e\u043d\u0435 \u0440\u0438\u0441\u043a\u0430'), (b'TREATMENT', '\u0418\u0434\u0435\u0442 \u043b\u0435\u0447\u0435\u043d\u0438\u0435'), (b'DANGER', '\u041d\u0443\u0436\u043d\u043e \u043b\u0435\u0447\u0435\u043d\u0438\u0435'), (b'OK', '\u0412\u0441\u0451 \u043e\u043a')]),
        ),
    ]
