# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_meeting'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='type',
            field=models.CharField(default=b'REGULAR', max_length=100, choices=[(b'REGULAR', '\u0411\u043e\u043b\u044c\u0448\u043e\u0439 \u043c\u0430\u0440\u0430\u0444\u043e\u043d\u0441\u043a\u0438\u0439 \u043c\u0438\u0442\u0438\u043d\u0433'), (b'NEWBY', '\u041d\u043e\u0432\u0438\u0447\u043a\u043e\u0432\u044b\u0439 \u043c\u0438\u0442\u0438\u043d\u0433')]),
        ),
    ]
