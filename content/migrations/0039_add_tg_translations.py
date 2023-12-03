# Generated by Django 3.1 on 2020-08-18 21:16

from django.db import migrations


def set_my_defaults(apps, schema_editor):
    TGTranslation = apps.get_model('content', 'TGTranslation')

    for key, (description, translation) in DEFAULT_TRANSLATION.items():
        TGTranslation.objects.update_or_create(
            key=key, defaults={'translation': translation, 'description': description}
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0038_meeting_order_num'),
    ]

    operations = [
        migrations.RunPython(set_my_defaults, reverse_code=migrations.RunPython.noop),
    ]


DEFAULT_TRANSLATION = {
    'BACK_TO_MAIN_MENU_BY_TIMEOUT': (
        "Промежуточный узел для редиректа по таймауту в главное меню",

        "Вернуться в Главное Меню."
    ),
    'BACK_TO_MAIN_MENU_BY_TIMEOUT__TXT': (
        "описание текста, выводимого при возврате в Главное Меню по таймауту",

        "Лимит времени в этом меню - один час. Вы перенаправлены в главное меню, вопрос не был отправлен команде. Пожалуйста, выберите правильную тему и задайте вопрос повторно."
    ),
}
