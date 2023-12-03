# coding=utf-8
from datetime import date, timedelta

from crm.models import RenewalRequest


def is_renewal_possible(user):
    # if valid_until is more than 8 weaks ahead - no
    # TODO: update rejection_reasons according to new chat bot
    if not user.profile.is_active:
        return False, "Ваш аккаунт на данный момент неактивен"

    if not user.profile.valid_until:
        return False, "Продолжать может только тот, кто уже начал!"

    if not user.profile.wave:
        return False, "Подписочные тарифы продлеваются автоматически. Уведомлять команду нет необходимости."

    diff = (user.profile.valid_until - date.today()).days

    # Участникам, у которых valid_until > NOW+23d, выдаем уведомление о том, что еще слишком рано
    if diff > 23:
        return False, "Обработка продлений вашего потока еще не началась.  " \
                      "Пожалуйста, напишите мне об этом через {days} д. ".format(days=diff - 23)

    # Участникам, у которых valid_until < NOW+10d, выдаем уведомление, что уже поздно
    if diff < 10:
        return False, "Обработка продлений вашего потока уже завершена. " \
                      "По моим данным, вам должна быть открыта оплата. Важно успеть оплатить до {valid_until}. " \
                      "Если что-то пошло не так - уточните, пожалуйста, у команды по ветке \"Задать вопрос\".".format(valid_until=user.profile.valid_until)

    existing_request = RenewalRequest.objects.filter(
        user=user,
        date_added__gte=user.profile.valid_until - timedelta(weeks=8)
    ).exclude(
        status='REJECTED'
    ).first()

    if existing_request:
        # FIXME: несовпадение типов, возвращаемых функцией
        return existing_request, None

    return True, None
