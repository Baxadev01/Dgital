# -*- coding: utf-8 -*-
# import logging

import csv
from collections import OrderedDict
from datetime import datetime, timedelta, date
from decimal import Decimal
from time import time

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Max
from django.forms import ValidationError
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from markdownx.utils import markdownify

from content.utils import get_user_meetings
from crm.models import Application, Campaign
from crm.utils.renewal import is_renewal_possible
from crm.utils.subscription import get_subscription_tariffS_data, get_subscription_changing_data
from srbc.decorators import validate_user, has_desktop_access
from srbc.forms import UserSettingsForm
from srbc.models import Checkpoint, UserReport
from srbc.models import DiaryRecord, UserNote, Wave, User, Profile, CheckpointPhotos
from srbc.models import SRBCImage, ParticipationGoal
from srbc.serializers.general import ProfileSerializer
from srbc.tasks import update_diary_trueweight
from srbc.utils.checkpoint_measurement import get_current_checkpoint_date
from srbc.views.api.v1.analytics import set_task_for_report_generation
from srbc.xiaomi import XiaomiManager

try:
    import http.client as http_client
except ImportError:
    import http.client as http_client

USER_MUST_SEE_WIDGETS = [
    'CALENDAR',
    'MEETINGS',
    'ALARM',
    'NOTES',
    'CHARTS',
]


def is_newbie(user):
    last_campaign = Campaign.objects.filter(start_date__lte=date.today()).order_by('-start_date').first()

    last_waves = [
        last_campaign.wave_chat,
        last_campaign.wave_channel,
    ]

    #if campaign does not have waves - no newbies are there
    if last_waves[0] is None or last_waves[1] is None:
        return False

    if not user.profile.is_active:
        return False

    if not user.profile.wave in last_waves:
        return False

    if user.membership.filter(chat__is_active=True, status__in=['JOINED']).count():
        return False

    return True

def get_recommendation_texts(note):
    texts = []

    if note.adjust_fruits == 'EXCLUDE':
        texts.append(
            {
                'title' : 'Замена моно- и дисахаридов',
                'description' : 
                    """Фрукты  
Проект рекомендует заменять фрукты и десерты в рационе на полную порцию овощей и/или, эпизодически, 2-5 г отрубей/шелухи псиллиума (отруби/шелуху псиллиума только на второй завтрак). 
Исключить полностью, как в свежем, так и сушеном виде: виноград, финики, инжир, изюм, хурму, бананы.

Иногда можно брать 170 грамм незапасающих овощей и дополнять их 30 граммами фруктов.  
Белковая часть второго завтрака остается неизменной при любых заменах и сочетаниях фруктов и овощей.

Сухофрукты  
Любых фабричных и покупных сухофруктов необходимо избегать. 
Допустимы сухофрукты, сделанные самостоятельно. Их в пищевой дневник нужно вносить как свежие фрукты - по массе исходного сырья. 

Добавленные простые сахара (моно- и дисахариды: сахароза, глюкоза, лактоза, фруктоза)  
Добавленные простые сахара, как в чистом виде, так и в продуктах, из рациона лучше убрать.

Овощи  
Проект рекомендует сочетать в порции запасающие и незапасающие овощи. Незапасающие должны преобладать или могут составлять порцию целиком.   


То есть морковь, свеклу, зеленую фасоль, тыкву, кукурузу, белокочанную капусту, горошек и другие углеводистые овощи не используйте как самостоятельный компонент. Составляйте порцию овощей так, чтобы доля этих продуктов в каждой порции была менее 50% от всей порции овощей. Никогда не используйте картофель во второй завтрак и на полдник.
                    """
            }
        )
    if note.adjust_fruits == 'RESTRICT':
        texts.append(
            {
                'title' : 'Минимизация моно- и дисахаридов',
                'description' : 
                    """Фрукты  
Необходимо сделать порцию фруктов не более 100 г на прием пищи. 
Исключить полностью, как в свежем, так и сушеном виде: виноград, финики, инжир, изюм, хурму, бананы. К такой порции фруктов можно добавить 100 г незапасающих овощей.

Сухофрукты:  
Любых фабричных и покупных сухофруктов необходимо избегать. 
Допустимы сухофрукты, сделанные самостоятельно. Их в пищевой дневник нужно вносить как свежие фрукты - по массе исходного сырья. 

При желании фрукты можно заменить на полную порцию овощей.

Добавленные простые сахара:  
Рекомендуем исключить, как в чистом виде, так и в продуктах, добавленные простые сахара (моно-, дисахариды): сахарозу, глюкозу, лактозу, фруктозу, а также различные олигосахариды.

Овощи:  
Проект рекомендует сочетать в порции запасающие и незапасающие овощи. Незапасающие должны преобладать или могут составлять порцию целиком.   

То есть морковь, свеклу, зеленую фасоль, тыкву, кукурузу, белокочанную капусту, горошек и другие углеводистые овощи не используйте как самостоятельный компонент. Составляйте порцию овощей так, чтобы доля этих продуктов в каждой порции была менее 50% от всей порции овощей. Никогда не используйте картофель во второй завтрак и на полдник.
                    """
            }
        )
    
    if note.adjust_carb_bread_min:
        texts.append(
            {
                'title' : 'Уменьшение полисахаридов',
                'description' : 
                    """Необходимо сделать порцию хлеба 25 грамм (на порцию эквивалент не более чем 20 грамм муки) и исключить хлеб и сложные углеводы в любом виде из состава ужина. Напоминаем, что картофель считается источником углеводов и увеличивает количество крахмала в приеме пищи.
                    """
            }
        )
    
    if note.adjust_carb_bread_late:
        texts.append(
            {
                'title' : 'Убрать полисахариды из ужина',
                'description' : 
                    """Необходимо исключить хлеб и сложные углеводы в любом виде из состава ужина.  Напоминаем, что картофель считается источником углеводов и увеличивает количество крахмала в приеме пищи.
                    """
            }
        )
    
    if note.adjust_carb_carb_vegs:
        texts.append(
            {
                'title' : 'Исключить запасающие овощи после обеда',
                'description' : 
                    """Необходимо исключить хлеб, сложные углеводы в любом виде и запасающие овощи из состава ужина. Последнее время для запасающих овощей - обед (до 14.30).
                    """
            }
        )
    
    if note.exclude_lactose:
        texts.append(
            {
                'title' : 'Исключить молочные сахара',
                'description' : 
                    """Рекомендуем полностью убрать молоко из рациона, оставить только молочнокислые продукты.
                    """
            }
        )
    
    if note.adjust_carb_mix_vegs:
        texts.append(
            {
                'title' : 'Смешивать овощи',
                'description' : 
                    """Морковь, свеклу, зеленую фасоль, тыкву, кукурузу, белокочанную капусту, горошек и другие углеводистые овощи не используйте как самостоятельный компонент, доля этих продуктов в каждой порции должна быть менее 50% от всей порции овощей. Никогда не используйте картофель во второй завтрак и на полдник.
                    """
            }
        )

    if note.restrict_lactose_casein:
        texts.append(
            {
                'title' : 'Ограничивать молочные сахара и казеин вторым завтраком',
                'description' : 
                    """Рекомендуем убрать молоко и молочнокислые продукты из рациона в любые приемы пищи, кроме второго завтрака.
                    """
            }
        )

    if note.adjust_calories != 0:
        sign = "+" if note.adjust_calories > 0 else '-'
        texts.append(
            {
                'title' : 'Корректировка калорийности рациона',
                'description' : 
                    """Рекомендованная норма всех навесок во все приемы пищи {sign}{percent}% от методички
                    """.format(
                        percent=abs(note.adjust_calories),
                        sign=sign
                    )
            }
        )

    if note.adjust_protein != 0:
        sign = "+" if note.adjust_protein > 0 else '-'
        texts.append(
            {
                'title' : 'Корректировка белка в рационе',
                'description' : 
                    """Рекомендованная норма навесок белкового продукта во все приемы пищи {sign}{percent}% от методички
                    """.format(
                        percent=abs(note.adjust_protein),
                        sign=sign
                    )
            }
        )

    if note.add_fat:
        texts.append(
            {
                'title' : 'Добавлять жиры',
                'description' : 
                    """1. Используйте молочные продукты полной жирности.
2. Добавляйте в качестве добавки омегу-3 или рыбий жир, а также лецитин, регулярно, всегда.
3. В обед иногда можно добавлять крупы или макароны в дополнение к полному обеду (не исключая хлеб).
4. На второй завтрак иногда можно 20 грамм орехов или семечек. Не исключайте при этом творог.
5. Добавляйте жиры в овощи 10-20 грамм в каждый прием пищи.
6. Иногда можно использовать зерновой хлеб, не делая его основным типом хлеба.

В ваших рационах техническая пометка «дополнительные продукты» при добавлении жиров является нормой.
                    """
            }
        )

    if note.adjust_carb_sub_breakfast:
        texts.append(
            {
                'title' : 'Завтрак по схеме обеда',
                'description' : 
                    "Необходимо сделать завтрак по схеме обеда (100 г белка, 200 г овощей, хлеб)"
            }
        )

    return texts

@login_required
@has_desktop_access
@validate_user
def dashboard(request):
    user = request.user

    application = Application.objects.filter(user=user).first()

    # if not instagram_linked and not request.user.profile.instagram_link_code:
    #     request.user.profile.instagram_link_code = hashlib.sha384(
    #         '%s-%s-%s' % (request.user.pk, uuid.uuid4(), int(round(time() * 1000)))).hexdigest()
    #
    #     while Profile.objects.filter(instagram_link_code=request.user.profile.instagram_link_code).exists():
    #         request.user.profile.instagram_link_code = hashlib.sha384(
    #             '%s-%s-%s' % (request.user.pk, uuid.uuid4(), int(round(time() * 1000)))).hexdigest()
    #     request.user.profile.save(update_fields=['instagram_link_code'])

    today = datetime.now()

    last_checkpoint_photos_date = CheckpointPhotos.objects.filter(
        user=request.user
    ).exclude(
        status='REJECTED'
    ).aggregate(
        last_checkpoint=Max('date')
    )

    last_checkpoint_photos_date = last_checkpoint_photos_date.get('last_checkpoint')

    last_recommendation = UserNote.objects.filter(
        label='IG', user=user, date_added__lte=timezone.now(), is_published=True
    ).order_by('-date_added').first()

    unfilled_checkpoint_exists = Checkpoint.objects.filter(user=request.user, is_editable=True).exists()

    today = timezone.localtime().date()

    if unfilled_checkpoint_exists:
        # не грузим юзера лишним уведомлением, так как уже есть уведомление о том, что есть незаполненный чекпоинт.
        need_to_create_checkpoint = False
    else:
        two_weeks_ago = today - timedelta(days=14)
        need_to_create_checkpoint = not Checkpoint.objects.filter(user=request.user, date__gte=two_weeks_ago).exists()

    last_rejected_checkpoint = None
    collage_required = False

    days_for_renewal = 10 if request.user.profile.is_in_club else 24
    renewal_request_possible, deny_reason = is_renewal_possible(request.user)
    renewal_required = (renewal_request_possible == True) \
                       and (request.user.profile.valid_until - date.today() < timedelta(days=days_for_renewal))

    active_tariff = request.user.profile.tariff

    if (request.user.profile.is_in_club and request.user.profile.is_perfect_weight) \
            or (active_tariff and not active_tariff.tariff_group.is_wave):
        checkpoint_required = False
    else:
        next_active_checkpoint_date, is_editable = get_current_checkpoint_date(
            wave_start_date=request.user.profile.wave.start_date, tz=request.user.profile.timezone
        )

        if last_checkpoint_photos_date:

            # проверим случай, когда замеры еще на модерации
            on_moderation = CheckpointPhotos.objects. \
                filter(user=request.user, status='NEW', date__gte=last_checkpoint_photos_date).exists()

            next_checkpoint_date_delta = next_active_checkpoint_date - last_checkpoint_photos_date
            checkpoint_required = False

            if checkpoint_required:
                last_rejected_checkpoint = CheckpointPhotos.objects.filter(
                    user=request.user, status='REJECTED', date__gte=last_checkpoint_photos_date
                ).first()

            collage_exists = SRBCImage.objects.filter(
                user=request.user,
                image_type__in=[
                    'CHECKPOINT_PHOTO',
                    'CHECKPOINT_PHOTO_FRONT',
                    'CHECKPOINT_PHOTO_SIDE',
                    'CHECKPOINT_PHOTO_REAR',
                ],
                date=last_checkpoint_photos_date
            ).exists()

            if on_moderation:
                collage_required = False
            else:
                collage_required = not collage_exists
        else:
            # необходимы стартовые фотографии
            checkpoint_required = True
            last_rejected_checkpoint = CheckpointPhotos.objects.filter(
                user=request.user, status='REJECTED'
            ).last()

        if last_rejected_checkpoint:
            last_rejected_checkpoint.rejection_reasons_display = []
            for reason in last_rejected_checkpoint.rejection_reasons:
                last_rejected_checkpoint.rejection_reasons_display.append(
                    dict(CheckpointPhotos.REJECTION_REASON_CHOICES).get(reason, reason)
                )

    yesterday = today - timedelta(days=1)

    payment_required = False

    if request.user.application.is_payment_allowed \
            and request.user.profile.valid_until - date.today() < timedelta(days=14):
        payment_required = True

    # Checking for telegram linked account
    telegram_user = True

    # Checking for chats to join
    chat_to_join = request.user.membership.filter(chat__is_active=True, status__in=['ALLOWED', 'LEFT']).first()

    user_notes_filter = UserNote.objects \
        .filter(user=request.user, is_published=True, date_added__lte=timezone.now()) \
        .exclude(label__in=['DOC', ]) \
        .order_by("-date_added")

    user_notes = user_notes_filter.all()[:3]
    user_notes_count = user_notes_filter.count()
    for note in user_notes:
        note.content = markdownify(note.content)

    user_widgets = request.user.profile.widgets_display

    for widget in USER_MUST_SEE_WIDGETS:
        if widget not in user_widgets:
            user_widgets.append(widget)

    widgets_data = {i: {} for i in user_widgets if i in user.profile.available_widgets}

    if 'ALARM' in widgets_data:
        widgets_data['ALARM'] = {
            'warning_flags': [
                'TEST',
                'OBSERVATION',
                'DANGER',
                'TREATMENT',
                'PR',
                'OOC',
            ]
        }

    # специальный блок для пояснения ряда рекоммендаций
    last_note = UserNote.objects.filter(
        label='IG',
        user=request.user,
        is_published=True,
        # date_added__date__lt=today - timedelta(days=1)
    ).order_by('-date_added').first()

    notes_description = []
    if last_note:
        notes_description = get_recommendation_texts(last_note)
        for note in notes_description:
            note['description'] = markdownify(note['description'])
    if 'NOTES' in widgets_data:
        widgets_data['NOTES'] = {
            'notes': user_notes,
            'notes_count': user_notes_count,
            'notes_description':  notes_description
        }

    if 'MEETINGS' in widgets_data:
        widgets_data['MEETINGS'] = {
            'meetings': get_user_meetings(request.user)[:5],
        }

    # print widgets_data

    return render(request, 'srbc/dashboard_user.html', {
        'telegram_user': telegram_user,

        'checkpoint_required': checkpoint_required,
        'last_checkpoint_photos_date': last_checkpoint_photos_date,
        'unfilled_checkpoint_exists': unfilled_checkpoint_exists,
        'need_to_create_checkpoint': need_to_create_checkpoint,
        'last_rejected_checkpoint': last_rejected_checkpoint,
        'payment_required': payment_required,
        'collage_required': collage_required,
        'renewal_required': renewal_required,

        'last_recommendation': last_recommendation,

        'is_newbie': is_newbie(user),

        'chat_to_join': chat_to_join,

        'application': application,
        'today': today,
        'yesterday': yesterday,

        'widgets_data': widgets_data,
    })


@login_required
@has_desktop_access
def profile(request, username=None):
    user = request.user

    if username:
        if username[:1] == '!' and user.is_staff:
            profile_user = User.objects.filter(id=username[1:]).select_related('profile').first()
            if profile_user:
                return redirect('/profile/%s/' % profile_user.username)
        else:
            profile_user = User.objects.filter(username__iexact=username).select_related('profile').first()

        if not profile_user:
            raise Http404()
    else:
        profile_user = None

    if user.is_staff and not request.GET.get('public'):
        return profile_admin(request, profile_user)
    else:
        if profile_user is None:
            raise Http404()

    if user != profile_user and not user.is_staff:
        raise Http404()
    if not user.groups.filter(name='Participant').exists():
        raise Http404()

    return profile_public(request, profile_user)


def convert_to_table_measurements(measurements):
    """ Для заданных измерений составляет данные для построения таблицы.

    :param measurements:
    :type measurements: list(srbc.models.Checkpoint)
    :return: табличные данные с дельтами {'rows': {...}, 'dates': [...]}
    :rtype: dict
    """
    if not measurements:
        return {}

    def _calculate(a, b, add=True):
        """ Вспомогательная функция для сложения/вычитания, оперирующая с None."""
        try:
            return (a + b) if add else (a - b)
        except TypeError:
            # какой-нибудь из замеров может быть None, тогда результат операции - None
            return None

    # названия замеров от 01 до 16го
    titles = ['Шея', 'Рука вверху, у подмышечной впадины', 'Середина бицепса', 'Над самым локтем',
              'Запястье', 'Над грудью', 'Грудь по линии сосков', 'Под грудью',
              'Талия', 'Живот в самом широком месте',
              'Ягодицы в самом широком месте',
              'Нога вверху, максимальный объем', 'Середина бедра', 'Колено над суставом',
              'Голень, максимальный обхват', 'Щиколотка, минимальный обхват', 'Рост']

    # Витьеватая логика дабы не тащить зависимость numpy.
    # 1) Проходимся по всем названиям замеров и составляем список данных для строки таблицы, где
    # для каждый даты представлен cписок [замер, дельта относительно стартового, дельта относительно предыдущего]
    # 2) Вместе с подчетом п1. подсчитываем рузультирующую строку сумм для каждой даты
    # (сумма замеров за дату, сумма относительно стартовой сумму замеров, сумма относителньо предыдущей суммы замеров)
    rows = OrderedDict()
    sums = []
    dates = []
    enumerated_measurements = list(enumerate(measurements[1:], 1))  # для того, чтобы каждый раз не считать заново
    for i in range(len(titles)):
        # замер для текущей строки
        if i < len(titles) - 1:
            attr = 'measurement_point_%02d' % (i + 1)
        else:
            # последний замер - это рост
            attr = 'measurement_height'

        start_value = getattr(measurements[0], attr)
        if start_value is not None:
            start_value = Decimal(start_value) / 10

        prev_value = start_value

        # замеры за дату старта
        columns = [[start_value, 0, 0]]
        if i == 0:
            dates.append(measurements[0].date)
            sums.append([start_value, 0, 0])
        else:
            # накапливаем сумму для значения стартовых замеров
            sums[0][0] = _calculate(sums[0][0], start_value)
            # дельта здесь (0, 0), поэтому не обновляем

        # замеры за остальные даты
        for n, m in enumerated_measurements:
            value = getattr(m, attr)
            if value is not None:
                value = Decimal(value) / 10
            start_diff = _calculate(start_value, value, add=False)
            prev_diff = _calculate(prev_value, value, add=False)
            prev_value = value

            columns += [[value, start_diff, prev_diff]]

            if i == 0:
                # в первой иттерации заполняем все начальные значения
                dates.append(m.date)
                sums.append([value, start_diff, prev_diff])
            else:
                # обновляем сумму замеров, сумму относительно стартовой суммы, сумму относительно предыдущего замера
                sums[n][0] = _calculate(sums[n][0], value)
                sums[n][1] = _calculate(sums[0][0], sums[n][0], add=False)
                sums[n][2] = _calculate(sums[n - 1][0], sums[n][0], add=False)

        rows.update({titles[i]: columns})

    rows.update({'Сумма': sums})
    return {'rows': rows, 'dates': dates}


def profile_admin(request, user):
    waves = Wave.objects.all()
    if user:
        profile = user.profile
        profile_serialized = ProfileSerializer(profile)
        profile_serialized_data = profile_serialized.data

        user_notes = UserNote.objects.filter(user=user).exclude(
            label=UserNote.LABEL_DOC).order_by('-date_added').select_related('author').all()
        user_docs = UserNote.objects.filter(user=user, label=UserNote.LABEL_DOC).order_by('-date_added').all()

        participation_goals = ParticipationGoal.objects.filter(user=user).order_by('-created_at').all()

        measurements = list(Checkpoint.objects.filter(user=user).order_by('date').all())
        measurements_data = convert_to_table_measurements(measurements=measurements)

        for note in user_notes:
            note.content = markdownify(note.content)

        for note in user_docs:
            note.content = markdownify(note.content)

        for goal in participation_goals:
            goal.text = markdownify(goal.text)
            goal.status_text = next(item[1] for item in ParticipationGoal.STATUSES if item[0] == goal.status)

    else:
        user_notes = []
        user_docs = []
        participation_goals = []
        profile_serialized_data = 'false'
        measurements_data = {}

    return render(request, 'srbc/profile_admin.html', {
        "waves": waves,
        "profile_user": user,
        "profile_serialized": profile_serialized_data,
        "user_notes": user_notes,
        "user_docs": user_docs,
        "participation_goals": participation_goals,
        "measurements_data": measurements_data,
    })


def profile_public(request, user):
    if user:
        profile = user.profile
        profile_serialized = ProfileSerializer(profile)

        measurements = list(Checkpoint.objects.filter(user=user).order_by('date').all())
        measurements_data = convert_to_table_measurements(measurements=measurements)

    else:
        raise Http404()

    return render(request, 'srbc/profile.html', {
        "profile_user": user,
        "profile_serialized": profile_serialized.data,
        "measurements_data": measurements_data,
    })


@login_required
@has_desktop_access
@validate_user
def load_true_weight(request):
    result = {
        "status": None,
    }

    if request.user.profile.trueweight_id:
        tw_id = request.user.profile.trueweight_id.split('-')
    else:
        tw_id = ['', '', '']

    if request.method == 'POST':
        if request.POST.get('action') == 'import':
            try:
                tw_id = request.POST.getlist('trueweight_id')
                if len(tw_id) != 3:
                    raise ValidationError('Неверный код')

                tw_data = requests.get('http://www.trueweight.net/download/?pc1=%s&pc2=%s&pc3=%s' % tuple(tw_id))
                if tw_data.headers.get('Content-Type') != 'text/csv; charset=utf-8':
                    raise ValidationError('Не удалось загрузить данные')

                if tw_data.status_code != 200:
                    raise ValidationError('Не удалось загрузить данные')

                request.user.profile.trueweight_id = "-".join(tw_id)
                request.user.profile.save(update_fields=['trueweight_id'])

                tw_csv = tw_data.content

                records = csv.reader(tw_csv.decode().splitlines(), delimiter=',')
                records_list = list(records)
                imported_cnt = 0

                # заблочим сразу на весь цикл, чтобы лочить несколько раз
                with transaction.atomic():
                    # Locking
                    Profile.objects.select_for_update().get(user=request.user)

                    is_dirty = False

                    for row in records_list:
                        record_date = datetime.strptime(row[0], '%Y-%m-%d')
                        try:
                            diary = DiaryRecord.objects.get(user=request.user, date=record_date)
                        except ObjectDoesNotExist:
                            diary = DiaryRecord(
                                user=request.user,
                                date=record_date
                            )
                            is_dirty = True

                        if not diary.weight:
                            record_weight = Decimal(row[1]) / 1000
                            diary.weight = float(record_weight)
                            imported_cnt += 1
                            is_dirty = True

                        if is_dirty:
                            diary.save()

                update_diary_trueweight.delay(user_id=request.user.pk)
                result = {
                    'status': 'ok',
                    'message': 'Данные были успешно загружены (%s шт.)' % imported_cnt,
                }
            except ValidationError as e:
                result['status'] = 'error'
                result['message'] = e.message
        if request.POST.get('action') == 'export':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="SRBC-Trueweight Export.csv"'
            csv_writer = csv.writer(response)

            diaries = DiaryRecord.objects.filter(user=request.user).order_by('-date')
            for diary in diaries:
                if not diary.weight:
                    continue

                csv_writer.writerow([diary.date.strftime('%Y-%m-%d'), str(int(diary.weight * 1000))])

            return response

    return render(
        request,
        'srbc/trueweight.html',
        {
            "result": result,
            "trueweight_id": tw_id,
        }
    )


@login_required
@has_desktop_access
def profile_settings(request):
    if request.method == 'POST' and request.POST.get('action') == 'profile':
        form = UserSettingsForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            form = UserSettingsForm(instance=request.user.profile)

    else:
        form = UserSettingsForm(instance=request.user.profile)

    apple_connected = request.user.social_auth.filter(provider='apple-id').first()
    google_connected = request.user.social_auth.filter(provider='google-oauth2').first()
    jawbone_linked = request.user.social_auth.filter(provider='jawbone').exists()

    today = date.today()

    # собираем все данные
    # информацию о подписке показываем не всегда, сразу выделим случаи
    subscription_info_show = False
    if request.user.profile.active_subscription or \
            (request.user.profile.tariff and
             request.user.profile.tariff.tariff_group.is_wave and
             request.user.profile.tariff_renewal_from <= today):
        subscription_info_show = True

    can_renewal = False
    renewal_dates_text = False

    if request.user.profile.tariff_renewal_from:
        if request.user.profile.tariff_renewal_from <= today <= request.user.profile.tariff_renewal_until \
                and request.user.application.is_payment_allowed:
            can_renewal = True

        if today < request.user.profile.tariff_renewal_from:
            renewal_dates_text = True

    renewal_info_show = False
    if request.user.profile.tariff and \
            request.user.profile.tariff.tariff_group.is_wave and \
            request.user.profile.tariff_renewal_from <= today:
        renewal_info_show = True

    already_renewaled = False
    if request.user.profile.tariff and \
            request.user.profile.active_tariff_history and \
            request.user.profile.tariff.tariff_group.is_wave:
        # активный волновой пользователь, опредялем проплату
        # так же надо учесть, что не должно быть ТОЛЬКО оплаты в будущем
        # если есть подписка в статусе ACTIVE - переходит на нее
        # если есть next_th - то оплатил волновой тарифф
        if request.user.profile.next_tariff_history or request.user.profile.active_subscription:
            already_renewaled = True

    next_th_start_date = request.user.profile.valid_until + timedelta(
        days=1) if request.user.profile.valid_until else None

    # вынесем отдельно для проверки в js Блоке
    active_subscription_slug = request.user.profile.active_subscription.tariff.slug if request.user.profile.active_subscription else ""

    # подгружаем или данные для обновления подписки или просто базовые
    # если активен волновой тариф, то меняем попдиски в будущем и никакие вычисления апгрейдов не нужны
    if active_subscription_slug and not request.user.profile.active_tariff_history.tariff.tariff_group.is_wave:
        # может быть случай, когда в активной ТХ один тариф подписки, а в активной подписке - другой.
        # расчеты цены надо производить от активного в ТХ в таком случае
        if request.user.profile.active_tariff_history.tariff.slug != active_subscription_slug:
            subscription_tariffs_data = get_subscription_changing_data(
                request.user.profile.active_tariff_history.tariff,
                request.user.profile.active_tariff_history.valid_until)
        else:
            subscription_tariffs_data = get_subscription_changing_data(
                request.user.profile.active_subscription.tariff, request.user.profile.active_tariff_history.valid_until)
    else:
        subscription_tariffs_data = get_subscription_tariffS_data()

    return render(
        request,
        'srbc/settings_user.html',
        {
            "form": form,
            "apple_connected": apple_connected,
            "google_connected": google_connected,
            "jawbone_linked": jawbone_linked,
            "can_renewal": can_renewal,
            "subscription_info_show": subscription_info_show,
            "renewal_dates_text": renewal_dates_text,
            "renewal_info_show": renewal_info_show,
            "already_renewaled": already_renewaled,
            "next_th_start_date": next_th_start_date,
            "subscription_tariffs": subscription_tariffs_data,
            "active_subscription_slug": active_subscription_slug,
            'stripe_pk': settings.STRIPE_PUBLIC_KEY,
        }
    )


@login_required
@has_desktop_access
def user_notes(request):
    user = request.user

    user_notes_list = UserNote.objects \
        .filter(user=user, is_published=True, date_added__lte=timezone.now()) \
        .exclude(label__in=['DOC', ]) \
        .order_by("-date_added") \
        .all()

    for note in user_notes_list:
        note.content = markdownify(note.content)

    return render(request, 'srbc/user_notes.html', {
        'notes': user_notes_list,
    })


@login_required
@has_desktop_access
@validate_user
def link_mifit(request):
    result = {
        "status": None,
    }

    mifit_username = ''

    if request.user.profile.mifit_id:
        mifit_id = request.user.profile.mifit_id
        mifit_linked = True
        result = {
            'status': 'ok',
        }

    else:
        mifit_linked = False
        mifit_id = ''

    if not mifit_linked and request.method == 'POST':
        try:
            mifit_id = request.POST.get('mifit_uid')
            mifit_username = request.POST.get('mifit_username')
            try:
                int(mifit_id)
            except ValueError:
                raise ValidationError('Неверный UID')

            ts = int(round(time() * 1000))
            bot_uid = settings.MIFIT_SETTINGS['uid']
            base_ulr = "https://hm.mi-ae.com/"
            r_token = settings.MIFIT_SETTINGS['guid']
            method = "huami.health.band.userBasicInfo.searchUser"
            url = "%s%s.json?r=%s&t=%s" % (base_ulr, method, r_token, ts)
            xm = XiaomiManager()

            mifit_user_data = xm.post(
                url=url,
                data={
                    "appid": "2882303761517276168",
                    "callid": "%s" % ts,
                    "cv": settings.MIFIT_SETTINGS['cv'],
                    "device": "ios_10.3",
                    "device_type": "ios_phone",
                    "lang": "en",
                    "search_uid": mifit_id,
                    "timezone": "Europe/Moscow",
                    "userid": bot_uid,
                    "v": settings.MIFIT_SETTINGS['v'],
                }
            )

            mifit_user_info = mifit_user_data.get('data')

            if not mifit_user_info:
                raise ValidationError('Неверный UID')

            if mifit_user_info.get('username') != mifit_username:
                raise ValidationError('Указанное имя пользователя не совпадает с тем, которое сохранено в MiFit')

            mifit_id = mifit_user_info.get('uid')

            ts = int(round(time() * 1000))
            method = "huami.health.band.pushMessage.sendInvitation"
            url = "%s%s.json?r=%s&t=%s" % (base_ulr, method, r_token, ts)

            mifit_request_data = xm.post(
                url=url,
                data={
                    "appid": "2882303761517276168",
                    "callid": "%s" % ts,
                    "cv": settings.MIFIT_SETTINGS['cv'],
                    "device": "ios_10.3",
                    "device_type": "ios_phone",
                    "lang": "en",
                    "to_uid": mifit_id,
                    "timezone": "Europe/Moscow",
                    "userid": bot_uid,
                    "v": settings.MIFIT_SETTINGS['v'],
                }
            )

            if mifit_request_data.get('message') == 'success':
                request.user.profile.mifit_id = mifit_id
                request.user.profile.save(update_fields=['mifit_id'])
                mifit_linked = True
                result = {
                    'status': 'ok',
                    'message': 'Запрос на добавление в друзья был отправлен. '
                               'Подтверди, чтобы данные из MiFit начали подгружаться автоматически. '
                               '(И не забывай синхронизировать трекер!)',
                }
            else:
                raise ValidationError(mifit_request_data.get('message'))
        except ValidationError as e:
            result['status'] = 'error'
            result['message'] = e.message
    return render(
        request,
        'srbc/mifit_link.html',
        {
            "result": result,
            "mifit_uid": mifit_id,
            "mifit_username": mifit_username,
            "mifit_linked": mifit_linked,
        }
    )


@login_required
@has_desktop_access
@validate_user
def result_reports(request):
    if request.method == 'POST':
        set_task_for_report_generation(request.user)

    reports = UserReport.objects.filter(user=request.user).order_by('-date')[:5]
    return render(
        request,
        'srbc/user_reports.html',
        {
            "reports": reports,
        }
    )


def result_report_get(request, hashid):
    report = get_object_or_404(UserReport, hashid=hashid)
    return redirect(report.pdf_file.url)
