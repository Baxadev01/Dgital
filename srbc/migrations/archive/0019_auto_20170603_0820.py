# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0018_diaryrecord_is_na_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=100, choices=[(b'DOC', '\u0414\u043e\u043a / \u041e\u0431\u0441\u043b\u0435\u0434\u043e\u0432\u0430\u043d\u0438\u044f'), (b'IG', '\u0410\u043d\u0430\u043b\u0438\u0437 \u0418\u0413'), (b'CHAT', '\u041a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u0440\u0430\u0446\u0438\u043e\u043d\u0430'), (b'NB', '\u0421\u043b\u0443\u0436\u0435\u043d\u0431\u043d\u0430\u044f \u0437\u0430\u043c\u0435\u0442\u043a\u0430')])),
                ('content', models.TextField(default=b'', blank=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='notes_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='notes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='usernotes',
            name='author',
        ),
        migrations.RemoveField(
            model_name='usernotes',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserNotes',
        ),
    ]
