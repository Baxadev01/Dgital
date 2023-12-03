# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect

from crm.models import Application
from srbc.models import Profile, TariffGroup

MEETINGS_VIEWS = [
    'content:meetings-list',
    'content:meeting-playlist',
    'content:meeting-player',
    'content:meeting-chunk',
]


def validate_user(func):
    def wrap(request, *args, **kwargs):
        user = request.user
        view_name = request.resolver_match.view_name

        if user.is_authenticated:
            if user.profile:
                profile = user.profile
            else:
                profile = Profile(user_id=user.id)
                profile.save()

            if user.application:
                application = user.application
            else:
                application = Application(user_id=user.id)
                application.save()

            # TODO: переписать на проверку активной tariff_history
            if not user.is_staff:
                # Сначала проверяем, не новый ли это пользователь
                # Если так - перенаправляем на одну из страниц мастера регистрации
                if not application.first_name or not application.last_name:
                    #Новый - не заполнены поля в анкете
                    return HttpResponseRedirect('/names/')

                if profile.username_is_editable:
                    #Возможно, новый - имя пользователя нуждается в изменении
                    return HttpResponseRedirect('/username/')

                if not profile.telegram_id:
                    #Новый - не внесен в систему Telegram аккаунт
                    return HttpResponseRedirect('/telegram/')

                if not profile.birth_year:
                    #Новый - Анкета не содержит важных полей
                    return HttpResponseRedirect('/application/')

                if profile.is_blocked:
                    # не новый, но заблокирован ранее
                    return HttpResponseRedirect('/blocked/')

                if not profile.has_wave_tariff_history and not profile.active_tariff_history:
                    # Пользователь НЕ участвовал раньше в стартах (волнах)
                    # и НЕ участвует сейчас ни в чем, даже в подписке
                    # хоть и не новый, но нужно отправлять на визарда

                    # ЗАГЛУШКА - оставлено для только-мобильных пользователей
                    # if not user_has_meetings_access:
                    # if not application.tariff or not application.campaign:
                    #     return HttpResponseRedirect('/tariff/')


                    if not application.tariff or not application.campaign:
                        # Новый - не выбран тариф или дата старта
                        return HttpResponseRedirect('/tariff/')

                    #Проверки, нужно ли тестирование
                    is_tariff_silenced = True
                    if application.tariff:
                        is_tariff_silenced = application.tariff.tariff_group.communication_mode != TariffGroup.COMMUNICATION_MODE_CHAT

                    # тестирование нужно только в случае, если у пользователя
                    # - выбран тариф
                    # - установлена дата старта
                    # - тариф подразумевает общение в канале, а не в чате
                    # - тестирование еще не принято
                    admission_required = all([
                        application.tariff,
                        application.campaign,
                        is_tariff_silenced,
                        application.admission_status != 'ACCEPTED',
                    ])

                    if admission_required:
                        # if user_has_meetings_access:
                        #     if view_name in MEETINGS_VIEWS:
                        #         pass
                        #     elif application.campaign.start_date >= date.today():
                        #         return HttpResponseRedirect('/admission/')
                        # else:
                        return HttpResponseRedirect('/admission/')

                    if not profile.tariff:
                        # тариф выбран в анкете, но не оплачен и не попал в профиль
                        return HttpResponseRedirect('/payment/')



                #все, это точно не новый пользователь

                # Если это подписка на лекции - перенаправить на страницу лекций и не пускать никуда больше
                user_has_only_meetings_access = profile.is_active \
                                            and profile.tariff \
                                            and profile.tariff.tariff_group.meetings_access != TariffGroup.MEETINGS_NO_ACCESS \
                                            and profile.tariff.tariff_group.diary_access == TariffGroup.DIARY_ACCESS_READ

                # Важно: эта проверка работает, в отличие от метода all()
                # метод all() бросает exception, если у человека нет тарифа в профиле (возвращающиеся, но еще не оплатившие)

                if user_has_only_meetings_access:
                    if view_name not in MEETINGS_VIEWS and not profile.tariff.tariff_group.expertise_access:
                        return HttpResponseRedirect('/meetings/')
                else:
                    if not profile.tariff:
                        return HttpResponseRedirect('/blocked/')

        return func(request, *args, **kwargs)

    return wrap


def has_desktop_access(func):
    def wrap(request, *args, **kwargs):
        user = request.user

        if user.is_authenticated:

            # нет доступа к десктопу
            if not user.profile.has_desktop_access:
                return HttpResponseRedirect('/blocked/desktop/no-access/')

        return func(request, *args, **kwargs)

    return wrap


def is_channel_admin(user):
    if not user.is_authenticated:
        return False

    if not user.is_staff:
        return False

    if user:
        return user.groups.filter(name='ChannelAdmin').count()
    return False


def is_superuser(user):
    if not user.is_authenticated:
        return False

    if not user.is_staff:
        return False

    return user.is_superuser
