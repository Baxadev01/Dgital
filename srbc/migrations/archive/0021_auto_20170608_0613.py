# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0020_auto_20170606_1837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diaryrecord',
            name='user',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='diaries', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='profile',
            name='sugar_status',
            field=models.IntegerField(default=0, choices=[(0, '\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u044b \u0430\u043d\u0430\u043b\u0438\u0437\u044b'), (1, '\u0412 \u0437\u043e\u043d\u0435 \u0440\u0438\u0441\u043a\u0430'), (2, '\u0418\u0434\u0435\u0442 \u043b\u0435\u0447\u0435\u043d\u0438\u0435'), (3, '\u041d\u0443\u0436\u043d\u043e \u043b\u0435\u0447\u0435\u043d\u0438\u0435'), (99, '\u0412\u0441\u0451 \u043e\u043a')]),
        ),
        migrations.AlterField(
            model_name='usernote',
            name='label',
            field=models.CharField(max_length=100, choices=[(b'DOC', '\u0414\u043e\u043a / \u041e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u044f'), (b'IG', '\u0410\u043d\u0430\u043b\u0438\u0437 \u0418\u0413'), (b'CHAT', '\u041a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u0440\u0430\u0446\u0438\u043e\u043d\u0430'), (b'NB', '\u0421\u043b\u0443\u0436\u0435\u0431\u043d\u0430\u044f \u0437\u0430\u043c\u0435\u0442\u043a\u0430')]),
        ),
    ]
