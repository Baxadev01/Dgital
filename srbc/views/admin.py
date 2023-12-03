# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from operator import itemgetter
from urllib.parse import urlencode

import pandas as pd
import requests
from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, F, IntegerField, OuterRef, Q, Subquery, Value as V, When, Exists, Value
from django.db.models.aggregates import Count, Sum
from django.db.models.functions import Coalesce, ExtractDay, TruncDate, Least
from django.forms.utils import ErrorList
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings
from markdownx.utils import markdownify
from rest_framework.renderers import JSONRenderer

from content.models import AnalysisTemplate
from crm.models import RenewalRequest, TariffHistory
from srbc.forms import AnalysisAdminForm, ProductModerationForm, ProdamusPaymentForm
from srbc.models import DiaryMeal, DiaryMealFault, DiaryRecord, MealComponent, MealFault, MealNoticeTemplateCategory, \
    MealProduct, MealProductAlias, MealProductModeration, MealProductTag, Profile, ProfileTwoWeekStat, \
    ProfileWeightWeekStat, User, UserBookMark, UserNote, Wave, TariffGroup

from srbc.serializers.general import ProfileAdminSerializer, ProfileSerializer, UserProfileSerializer
from srbc.utils.diary import process_meal_component_by_product
from srbc.utils.personal_recommendation import get_faults_choices

logger = logging.getLogger(__name__)


class MealProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_staff:
            return MealProduct.objects.none()

        qs = MealProduct.objects.filter(is_verified=True, component_type__isnull=False).all()

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs


def check_ticket_title(title, user):
    """ Проверяет выполнение условия для title тикета:
            должен быть создан в базе продуктов продукт с таким названием,
            помечен как промодерированный, категория - пустая

    :param title:
    :type title: unicode
    :param user:
    :type user: srbc.models.User
    """
    # Должен быть создан в базе продуктов продукт с таким названием,
    # помечен как промодерированный, категория - пустая
    mp, is_created = MealProduct.objects.get_or_create(
        title=title,
        is_verified=True,
        component_type=None,
    )
    if is_created:
        mp.verified_at = timezone.now()
        mp.verified_by = user
        mp.save(update_fields=['verified_at', 'verified_by'])

    return mp


@login_required
def product_moderation(request):
    if not request.user.is_staff:
        return redirect('/')

    lock_time = 15
    ticket_id = request.GET.get('ticket')

    try:
        ticket_id = int(ticket_id)
    except (TypeError, ValueError):
        ticket_id = None

    ticket = None

    if ticket_id:
        try:
            ticket = MealProductModeration.objects.get(pk=ticket_id)

            ticket.read_only = False

            if ticket.status != 'PENDING':
                ticket.read_only = True

            if ticket.moderator_id and ticket.moderator_id != request.user.id:
                if ticket.moderated_at >= timezone.now() - timedelta(minutes=lock_time):
                    ticket.read_only = True

            if not ticket.read_only:
                ticket.moderator_id = request.user.id
                ticket.moderated_at = timezone.now()
                ticket.save(update_fields=['moderator_id', 'moderated_at'])
        except ObjectDoesNotExist:
            ticket_id = None

    if not ticket_id:
        next_ticket = MealProductModeration.objects.filter(status='PENDING') \
            .filter(
            Q(moderator_id=request.user.id) | Q(moderator_id__isnull=True),
            Q(moderated_at__lte=timezone.now() - timedelta(minutes=lock_time))
            | Q(moderator_id__isnull=True)
            | Q(moderator_id=request.user.id)
        ).order_by('added_at', F('moderated_at').asc(nulls_last=True)).first()

        if not next_ticket:
            return render(request, 'srbc/product_moderation.html', {
                "ticket": None,
                "form": None,
            })
        return redirect('./?ticket=%s' % next_ticket.pk)

    if request.method == 'POST' and not ticket.read_only:
        form = ProductModerationForm(data=request.POST, instance=ticket)
        if form.is_valid():
            # APPROVED_NEW
            if form.cleaned_data.get('status') == 'APPROVED_NEW':
                # create new product
                new_product = MealProduct(
                    title=form.cleaned_data['title'],
                    component_type=form.cleaned_data['component_type'],
                    is_fast_carbs=form.cleaned_data['is_fast_carbs'],
                    is_alco=form.cleaned_data['is_alco'],
                    protein_percent=form.cleaned_data['protein_percent'] or 0,
                    fat_percent=form.cleaned_data['fat_percent'] or 0,
                    carb_percent=form.cleaned_data['carb_percent'] or 0,
                    verified_at=timezone.now(),
                    verified_by=request.user,
                    is_verified=True,
                )
                new_product.save()

                # update components with new product
                meal_components_to_fix = MealComponent.objects.filter(
                    other_title__iexact=ticket.title_source, component_type='new'
                ).all()

                for _component in meal_components_to_fix:
                    if new_product.component_type in ('unknown', 'mix'):
                        _component = process_meal_component_by_product(_component, new_product)
                    else:
                        _component.component_type = new_product.component_type
                        _component.other_title = new_product.title
                        _component.meal_product = new_product

                    _component.save()

                # update ticket
                ticket.title = new_product.title
                ticket.moderated_at = timezone.now()
                ticket.moderator_id = request.user.id
                ticket.status = 'APPROVED_NEW'
                ticket.save()
                ticket.read_only = True

            # APPROVED_ALIAS
            if form.cleaned_data.get('status') == 'APPROVED_ALIAS':
                alias_of = form.cleaned_data.get('alias_of')

                # FIXME: Алиас должен быть прописан к продукту в базе

                # update components
                meal_components_to_fix = MealComponent.objects.filter(
                    other_title__iexact=ticket.title_source, component_type='new'
                ).all()

                for _component in meal_components_to_fix:
                    _component.component_type = alias_of.component_type
                    _component.other_title = alias_of.title
                    _component.meal_product = alias_of
                    _component.save()

                # Алиас должен быть прописан к продукту в базе
                MealProductAlias(
                    title=ticket.title,
                    product=alias_of
                ).save()

                # update ticket
                ticket.title = alias_of.title
                ticket.moderated_at = timezone.now()
                ticket.moderator_id = request.user.id
                ticket.status = 'APPROVED_ALIAS'
                ticket.save()
                ticket.read_only = True

            # REJECTED
            # # REJECTED - REMOVE
            if form.cleaned_data.get('status') == 'REJECTED_REMOVE':
                # - Status = rejected
                # - Remove meal component from diary
                meal_components_to_fix = MealComponent.objects.filter(
                    other_title__iexact=ticket.title_source, component_type='new'
                ).all()

                # FIXME: Должен быть создан в базе продуктов продукт с таким названием,
                # помечен как промодерированный, категория - пустая

                for _component in meal_components_to_fix:
                    diary = _component.meal.diary

                    # обновим дневник
                    diary.meal_status = 'FAKE'
                    diary.is_fake_meals = True
                    diary.save(update_fields=['meal_status', 'is_fake_meals'])

                    # удалим компонент
                    _component.delete()

                check_ticket_title(title=ticket.title, user=request.user)

                # update ticket
                ticket.title = form.cleaned_data.get('title')
                ticket.meal_component_id = None
                ticket.moderated_at = timezone.now()
                ticket.moderator_id = request.user.id
                ticket.status = 'REJECTED_REMOVE'
                ticket.rejection_reason = form.cleaned_data.get('rejection_reason')
                ticket.save()
                ticket.read_only = True

            # # REJECTED - IGNORE
            # - Status = rejected
            # - set category according to nutrition (or unknown)
            if form.cleaned_data.get('status') == 'REJECTED_IGNORE':
                # FIXME: Должен быть создан в базе продуктов продукт с таким названием,
                # помечен как промодерированный, категория - пустая

                ticket.title = form.cleaned_data.get('title')
                ticket.moderated_at = timezone.now()
                ticket.moderator_id = request.user.id
                ticket.status = 'REJECTED_IGNORE'
                ticket.rejection_reason = form.cleaned_data.get('rejection_reason')
                ticket.save()
                ticket.read_only = True
                meal_components_to_fix = MealComponent.objects.filter(
                    other_title__iexact=ticket.title_source, component_type='new'
                ).all()

                meal_product = check_ticket_title(title=ticket.title, user=request.user)

                for _component in meal_components_to_fix:
                    if not _component.meal_product:
                        _component.meal_product = meal_product

                    _component.component_type = 'unknown'
                    _component = process_meal_component_by_product(_component)
                    _component.save(
                        update_fields=['component_type', 'description', 'other_title', 'meal_product_id'])

            # # REJECTED - REPLACE
            # - Status = rejected
            # - Find all "new" with same other_title, replace with product_by_id, set category according to product and nutrition
            if form.cleaned_data.get('status') == 'REJECTED_REPLACE':

                # FIXME: Должен быть создан в базе продуктов продукт с таким названием,
                # помечен как промодерированный, категория - пустая

                ticket.alias_of = form.cleaned_data.get('alias_of')
                product_to_place = ticket.alias_of
                if not product_to_place:
                    errors = form._errors.setdefault("__all__", ErrorList())
                    errors.append("Продукт не найден")
                else:
                    ticket.title = product_to_place.title
                    ticket.moderated_at = timezone.now()
                    ticket.moderator_id = request.user.id
                    ticket.status = 'REJECTED_REPLACE'
                    ticket.rejection_reason = form.cleaned_data.get('rejection_reason')
                    ticket.save()
                    ticket.read_only = True
                    meal_components_to_fix = MealComponent.objects.filter(
                        other_title__iexact=ticket.title_source, component_type='new'
                    ).all()

                    for _component in meal_components_to_fix:
                        if product_to_place.component_type in ['unknown', 'mix']:
                            _component.meal_product = product_to_place
                            _component.meal_product_id = product_to_place.pk
                            _component.component_type = product_to_place.component_type
                            _component.other_title = product_to_place.title
                            _component = process_meal_component_by_product(_component, product_to_place)
                            _component.save(
                                update_fields=['component_type', 'description', 'other_title', 'meal_product_id'])
                        else:
                            _component.meal_product_id = product_to_place.pk
                            _component.component_type = product_to_place.component_type
                            _component.other_title = product_to_place.title
                            _component.description = product_to_place.title
                            _component.save(
                                update_fields=['component_type', 'description', 'other_title', 'meal_product_id'])

                        check_ticket_title(title=ticket.title, user=request.user)

            # go to next ticket to moderate
            return redirect('/staff/meal_products/')

        else:
            print('OOPS')
            print(dict(request.POST))

        # ticket
    else:
        if ticket.meal_component:
            text = '<a href="%s" target="_blank">Ссылка, указанная пользователем</a>' % ticket.meal_component.external_link
            ProductModerationForm.base_fields['title'].help_text = text

            text = 'Данные от пользователя: %s г'
            if ticket.meal_component.details_carb:
                ProductModerationForm.declared_fields[
                    'carb_percent'].help_text = text % ticket.meal_component.details_carb

            if ticket.meal_component.details_protein:
                ProductModerationForm.declared_fields['protein_percent'].help_text = \
                    text % ticket.meal_component.details_protein

            if ticket.meal_component.details_fat:
                ProductModerationForm.declared_fields[
                    'fat_percent'].help_text = text % ticket.meal_component.details_fat

            ProductModerationForm.declared_fields['is_fast_carbs'].help_text = \
                'Данные от пользователя: %s' % ticket.meal_component.details_sugars

        form = ProductModerationForm(instance=ticket)

    if ticket.read_only:
        for field in form.fields:
            form.fields[field].disabled = True

    return render(request, 'srbc/product_moderation.html', {
        "form": form,
        "ticket": ticket,
    })


def get_filters_by_request(request_data, prefix=''):
    is_filtered = False
    bookmarked_only = False
    club_only = False
    stat_filter = None
    stat_filter_mode = None
    wave_id = None
    wave_title = None
    participation_mode = None
    wave_duration = None

    if '%sbookmarked' % prefix in request_data:
        bookmarked_only = True
        is_filtered = True

    if '%sclub' % prefix in request_data and request_data.get('%sclub' % prefix) in ['clubonly', 'noclub']:
        club_only = request_data.get('%sclub' % prefix)
        is_filtered = True

    if '%swave_duration' % prefix in request_data and request_data.get(
        '%swave_duration' % prefix) in [
            'lte_8_weeks', 'gt_8_weeks']:
        wave_duration = request_data.get('%swave_duration' % prefix)
        is_filtered = True

    if '%sparticipation_mode' % prefix in request_data and request_data.get(
        '%sparticipation_mode' % prefix) in [
            'chat', 'channel', 'non_wave']:
        participation_mode = request_data.get('%sparticipation_mode' % prefix)
        is_filtered = True

    if '%sstat_filter' % prefix in request_data \
            and request_data.get('%sstat_filter' % prefix) in [
                # 'to_meal',
                'to_analyze',
                # 'to_renew'
            ]:
        stat_filter_mode = request_data.get('%sstat_filter' % prefix)
        stat_filter = [
            key for key, value in Profile.STAT_GROUPS.items() if value[request_data.get('%sstat_filter' % prefix)]
        ]
        is_filtered = True

    if '%swave' % prefix in request_data:
        wave_id = Wave.objects.filter(title=request_data.get('%swave' % prefix)).values_list('pk', flat=True).first()
        if wave_id:
            wave_title = request_data.get('%swave' % prefix)
            is_filtered = True

    return is_filtered, bookmarked_only, club_only, stat_filter, stat_filter_mode, \
        wave_id, wave_title, participation_mode, wave_duration


@login_required
def users_list_new(request):
    if not request.user.is_staff:
        return redirect('/')

    bookmarked_ids = []
    srbc_users_base_stat = []
    cookies_to_set = {}
    cookies_to_delete = []
    wave_ids_in_list = set([])

    today = date.today()

    (is_filtered, bookmarked_only, club_flag, stat_filter, stat_filter_mode,
     wave_id, wave_title, participation_mode, wave_duration) = get_filters_by_request(request.GET)

    cookies_prefix = 'staff_users_'

    if is_filtered:
        if bookmarked_only:
            cookies_to_set['%sbookmarked' % cookies_prefix] = 1
        else:
            cookies_to_delete.append('%sbookmarked' % cookies_prefix)

        if club_flag:
            cookies_to_set['%sclub' % cookies_prefix] = club_flag
        else:
            cookies_to_delete.append('%sclub' % cookies_prefix)

        if stat_filter:
            cookies_to_set['%sstat_filter' % cookies_prefix] = stat_filter_mode
        else:
            cookies_to_delete.append('%sstat_filter' % cookies_prefix)

        if wave_id:
            cookies_to_set['%swave' % cookies_prefix] = wave_title
        else:
            cookies_to_delete.append('%swave' % cookies_prefix)

        if participation_mode:
            cookies_to_set['%sparticipation_mode' % cookies_prefix] = participation_mode
        else:
            cookies_to_delete.append('%sparticipation_mode' % cookies_prefix)

        if wave_duration:
            cookies_to_set['%swave_duration' % cookies_prefix] = wave_duration
        else:
            cookies_to_delete.append('%swave_duration' % cookies_prefix)

    else:
        query_params = {}
        (is_filtered, bookmarked_only, club_flag, stat_filter, stat_filter_mode, wave_id, wave_title,
         participation_mode, wave_duration) = get_filters_by_request(request.COOKIES, cookies_prefix)
        if is_filtered:
            if bookmarked_only:
                query_params['bookmarked'] = 1

            if club_flag:
                query_params['club'] = club_flag

            if participation_mode:
                query_params['participation_mode'] = participation_mode

            if wave_duration:
                query_params['wave_duration'] = wave_duration

            if stat_filter:
                query_params['stat_filter'] = stat_filter_mode

            if wave_id:
                query_params['wave'] = wave_title

            return redirect('/users/?%s' % urlencode(query_params))

    if is_filtered:
        srbc_users = User.objects
        th_filter_kwargs = {}

        th_filter_kwargs['valid_from__lte'] = today
        th_filter_kwargs['valid_until__gte'] = today
        th_filter_kwargs['is_active'] = True

        if club_flag == 'clubonly':
            th_filter_kwargs['tariff__tariff_group__is_in_club'] = True
        if club_flag == 'noclub':
            th_filter_kwargs['tariff__tariff_group__is_in_club'] = False

        # user_filter_kwargs - основная фильтрация, копируем все, что собрано из th_filter_kwargs и расширяем дальше фильтром
        # по волне для конкретной активной записи
        user_filter_kwargs = {'tariff_history__%s' % k: v for (k, v) in th_filter_kwargs.items()}

        # Для получения списка всех потоков
        th_filter_kwargs['tariff__tariff_group__is_wave'] = True

        if participation_mode == 'non_wave':
            user_filter_kwargs['tariff_history__tariff__tariff_group__is_wave'] = False
        else:
            user_filter_kwargs['tariff_history__tariff__tariff_group__is_wave'] = True
            if participation_mode == 'channel':
                user_filter_kwargs[
                    'tariff_history__tariff__tariff_group__communication_mode'] = TariffGroup.COMMUNICATION_MODE_CHANNEL

            if participation_mode == 'chat':
                user_filter_kwargs[
                    'tariff_history__tariff__tariff_group__communication_mode'] = TariffGroup.COMMUNICATION_MODE_CHAT
        
        if stat_filter_mode == 'to_analyze':
            mode_to_analyze = [
                TariffGroup.DIARY_ANALYZE_MANUAL, 
                TariffGroup.DIARY_ANALYZE_AUTO
            ]

            user_filter_kwargs['tariff_history__tariff__tariff_group__diary_analyze_mode__in'] = mode_to_analyze

        if bookmarked_only:
            bookmarked_users = UserBookMark.objects.filter(user=request.user)
            bookmarked_ids = [u.bookmarked_user_id for u in bookmarked_users]
            user_filter_kwargs['pk__in'] = bookmarked_ids
            th_filter_kwargs['user_id__in'] = bookmarked_ids

        if wave_id:
            user_filter_kwargs['tariff_history__wave_id'] = wave_id

        wave_ids_in_list = TariffHistory.objects.filter(**th_filter_kwargs).values_list('wave_id', flat=True).distinct()

        note_qs = UserNote.objects.filter(
            label='IG',
            user_id=OuterRef("pk"),
            is_published=True
        ).order_by("-date_added")

        srbc_users = srbc_users.filter(**user_filter_kwargs)

        if wave_duration:
            # применяем после фильтрации, tariff_history обрежется и будет только активная запись.

            # нужно именно беспрерывное участие пользовтаеля, несмотря на его переходы между форматами к примеру
            # беспрерывное участие можно вычислять от старта кампании,
            # если был перерыв участия, то будет новая кампания и так сможем вычислить бесспрерывное
            if wave_duration == 'lte_8_weeks':
                srbc_users = srbc_users.filter(
                    application__campaign__start_date__gte=today - timedelta(weeks=8)
                )

            else:
                srbc_users = srbc_users.filter(
                    application__campaign__start_date__lt=today - timedelta(weeks=8)

                )

        srbc_users_base_stat = srbc_users.annotate(
            last_note=Subquery(note_qs.values('date_added')[:1])
        ).select_related('profile', 'profile__group_leader')

        today = date.today()
        today_minus_7 = today - timedelta(days=6)

        if stat_filter_mode == 'to_analyze':
            # фильтруются только пользователи на автоматическом и ручном режиме, 
            # фильтр по этому критерию выше и вынесен отдельно со всеми фильтрами по ТХ
            srbc_users_base_stat = srbc_users_base_stat.filter(
                Q(last_note__lte=today_minus_7) | Q(last_note__isnull=True))

        srbc_users_mealsdata = srbc_users.annotate(
            meals_missed=Sum(
                Case(
                    When(
                        Q(diaries__is_meal_validated=True)
                        & Q(diaries__meal_status='PENDING')
                        & Q(diaries__is_fake_meals=False),
                        then=1
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ),
            meal_scores=Sum(
                Case(
                    When(
                        Q(diaries__meals__isnull=False)
                        & Q(diaries__date__gte=today_minus_7)
                        & Q(diaries__is_fake_meals=False)
                        & Q(diaries__is_meal_reviewed=True),
                        then='diaries__meals'
                    ),
                    default=0, output_field=IntegerField()
                )
            ),
            meal_faults=Sum(
                Case(
                    When(
                        Q(diaries__meals__isnull=False)
                        & Q(diaries__date__gte=today_minus_7)
                        & Q(diaries__is_fake_meals=False)
                        & Q(diaries__is_meal_reviewed=True),
                        then='diaries__faults'
                    ),
                    When(
                        Q(diaries__is_ooc=True)
                        & Q(diaries__date__gte=today_minus_7)
                        & Q(diaries__is_fake_meals=False)
                        & Q(diaries__is_meal_reviewed=True),
                        then=3
                    ),
                    default=0, output_field=IntegerField()
                )
            ),
            meals_count=Sum(
                Case(
                    When(
                        Q(diaries__is_meal_reviewed=True)
                        & Q(diaries__date__gte=today_minus_7)
                        & Q(diaries__is_fake_meals=False)
                        & Q(diaries__is_na_meals=False),
                        then=1
                    ),
                    default=0, output_field=IntegerField()
                )

            )
        ).all()

        user_weight_delta = ProfileWeightWeekStat.objects.filter(user__in=srbc_users)
        user_weight_stat = {}

        for user_stat in user_weight_delta:
            user_weight_stat[user_stat.user_id] = {
                'weight_days': user_stat.date_end - user_stat.date_start,
                'weight_delta':
                    (user_stat.weight_end - user_stat.weight_start) * 1000
                    if user_stat.weight_start and user_stat.weight_end
                    else None,
            }

        user_meals_stat = {}

        for user_meal_stat in srbc_users_mealsdata:
            user_meals_stat[user_meal_stat.pk] = {
                'meals_missed': user_meal_stat.meals_missed,
                'meal_scores': user_meal_stat.meal_scores,
                'meal_faults': user_meal_stat.meal_faults,
                'meals_count': user_meal_stat.meals_count,
            }

        srbc_users_base_stat = srbc_users_base_stat.order_by('-tariff_history__wave__start_date')

        for _user in srbc_users_base_stat:
            _user.is_bookmarked = _user.pk in bookmarked_ids

            if _user.pk in user_meals_stat:
                diary_stat = user_meals_stat[_user.pk]

                _user.meals_missed = diary_stat['meals_missed']
                _user.meal_faults = diary_stat['meal_faults']
                _user.meal_scores = diary_stat['meal_scores']
                _user.meals_count = diary_stat['meals_count']

            else:
                _user.meals_missed = 0
                _user.meal_faults = 0
                _user.meals_count = 0
                _user.meal_scores = 0

            if _user.meals_count:
                _user.meal_total_score = (4999 - _user.meal_faults * 100. / _user.meals_count) * 1e6
                _user.meal_total_score += (4999 + _user.meal_scores * 100. / _user.meals_count) * 100
                _user.meal_total_score += _user.meals_count
            else:
                _user.meal_total_score = 0

            if _user.pk in user_weight_stat:
                weight_stat = user_weight_stat[_user.pk]
                _user.weight_days = weight_stat['weight_days']
                _user.weight_delta = weight_stat['weight_delta']
            else:
                _user.weight_days = 0
                _user.weight_delta = 0

    waves = Wave.objects.filter(Q(is_in_club=False) | Q(pk=wave_id)).order_by('-start_date', 'title').all()

    waves_in_list = [k for k in waves if k.id in wave_ids_in_list]
    waves_not_in_list = [k for k in waves if k.id not in wave_ids_in_list]

    response = render(request, 'srbc/users_list_new.html', {
        "waves_in_list": waves_in_list,
        "waves_not_in_list": waves_not_in_list,
        "srbc_users": srbc_users_base_stat,
        "bookmarked_only": bookmarked_only,
        "club": club_flag,
        "stat_filter": stat_filter_mode,
        "is_filtered": is_filtered,
        "wave_id": wave_id,
        "participation_mode": participation_mode,
        "wave_duration": wave_duration
    })

    for cookie_name, cookie_value in cookies_to_set.items():
        response.set_cookie(cookie_name, cookie_value)

    for cookie_name in cookies_to_delete:
        response.delete_cookie(cookie_name)

    return response


@login_required
def diaries_form(request):
    user = request.user
    if not user.is_staff:
        return redirect('/')

    return render(request, 'srbc/diaries_data.html', {
    })


def dashboard_sergeant(request):
    return render(request, 'srbc/dashboard_sergeant.html', {
    })


def dashboard_rapid(request):
    return render(request, 'srbc/dashboard_rapid.html', {
    })


@login_required
def user_diaries_form(request, username):
    user = request.user
    if not user.is_staff:
        return redirect('/')

    profile_user = User.objects.filter(username=username).select_related('profile').first()
    if not profile_user:
        raise Http404()

    profile_serialized = UserProfileSerializer(profile_user)
    return render(
        request,
        'srbc/user_diaries.html',
        {
            "profile_user": profile_user,
            "profile_serialized": profile_serialized.data,
        }
    )


@login_required
def meal_admin(request, username):
    user = request.user
    if not user.is_staff:
        return redirect('/')

    profile_user = User.objects.filter(username=username).select_related('profile').first()
    if not profile_user:
        raise Http404()
    profile = profile_user.profile
    profile_serialized = ProfileSerializer(profile)
    profile_json = JSONRenderer().render(profile_serialized.data)

    return render(
        request,
        'srbc/user_meal_admin.html',
        {
            "profile_user": profile_user,
            "profile_serialized": profile_serialized.data,
        }
    )


@login_required
def meal_admin_stream_go(request):
    user = request.user
    today = timezone.now().date()
    if not user.is_staff:
        return redirect('/')

    meals_reviewed_today = DiaryRecord.objects.filter(
        meal_status__in=['DONE', 'FAKE'],
        meal_reviewed_by_id=request.user.id,
        meal_last_status_date__date=today,
    ).count()

    meals_left_auto = DiaryRecord.objects.filter(
        Q(meal_last_status_date__lte=timezone.now() + timedelta(minutes=10)) | Q(meal_last_status_date__isnull=True),
        meal_status__in=['PENDING', 'VALIDATION', 'FEEDBACK'],
        user__tariff_history__valid_until__gte=today,
        user__tariff_history__valid_from__lte=today,
        user__tariff_history__is_active=True,

        anlz_mode=DiaryRecord.ANLZ_MODE_AUTO
    ).distinct().count()

    meals_left_manual = DiaryRecord.objects.filter(
        Q(meal_last_status_date__lte=timezone.now() + timedelta(minutes=10)) | Q(meal_last_status_date__isnull=True),
        meal_status__in=['PENDING', 'VALIDATION', 'FEEDBACK'],

        user__tariff_history__valid_until__gte=today,
        user__tariff_history__valid_from__lte=today,
        user__tariff_history__is_active=True,

        anlz_mode=DiaryRecord.ANLZ_MODE_MANUAL
    ).distinct().count()

    return render(
        request,
        'srbc/go_meal_review.html',
        {
            "meals_reviewed_today": meals_reviewed_today,
            "meals_count_auto": meals_left_auto,
            "meals_count_manual" : meals_left_manual,
            "ref_mode_auto": DiaryRecord.ANLZ_MODE_AUTO,
            "ref_mode_manual": DiaryRecord.ANLZ_MODE_MANUAL,
        }
    )


@login_required
def meal_admin_stream(request, user_id, meal_date):
    user = request.user
    if not user.is_staff:
        return redirect('/')

    profile_user = User.objects.filter(pk=user_id).select_related('profile').first()

    if not profile_user:
        raise Http404()

    today = datetime.strptime(meal_date, "%Y-%m-%d").date()

    diary = DiaryRecord.objects.filter(date=today, user=profile_user).first()

    if diary and request.GET.get('lock'):
        if diary.meal_last_status_date and diary.meal_last_status_date >= timezone.now() - timedelta(minutes=10):
            return redirect('/staff/meal_review/')
        else:
            diary.meal_last_status_date = timezone.now()
            diary.save(update_fields=['meal_last_status_date'])
            return redirect('/user/%s/diaries/%s/meal/' % (user_id, meal_date))

    profile = profile_user.profile
    profile_serialized = ProfileAdminSerializer(profile)

    meals_left = 0

    pers_rec_note = UserNote.objects.filter(
        label='IG',
        user=profile_user,
        is_published=True,
        date_added__date__lt=today - timedelta(days=1)
    ).order_by('-date_added').first()

    notices_templates_categories = MealNoticeTemplateCategory.objects.filter(
        is_active=True,
        templates__is_active=True
    ).prefetch_related('templates').all()

    notices_dict = {
        _c.code: {
            "title": _c.title,
            "scope": _c.scopes,
            "templates": [
                {"text": _t.template} for _t in _c.templates.filter(is_active=True).all()
            ]
        }
        for _c in notices_templates_categories
    }

    possible_faults_list = get_faults_choices(pers_rec_note)

    meal_th = TariffHistory.objects.filter(
        user_id=user_id,
        valid_until__gte=meal_date,
        valid_from__lte=meal_date,
        is_active=True,
    ).first()

    meal_tariff = meal_th.tariff.title if meal_th else None

    return render(
        request,
        'srbc/user_meal_admin_stream.html',
        {
            "today": today,
            "meals_left": meals_left,
            "note": pers_rec_note,
            "profile_user": profile_user,
            "profile_serialized": profile_serialized.data,
            "notice_templates": notices_dict,
            "possible_faults_list": possible_faults_list,
            "meal_tariff" : meal_tariff
        }
    )


@login_required
def users_list_autoanalize(request):
    if not request.user.is_staff:
        return redirect('/')

    waves = Wave.objects.all()
    srbc_users = User.objects.filter(profile__is_active=True).filter(autoanalize__isnull=False)

    srbc_users_base_stat = srbc_users.select_related('profile', 'profile__wave', 'profile__group_leader', 'autoanalize')
    srbc_users_base_stat = list(srbc_users_base_stat)

    for userstat in srbc_users_base_stat:
        last_note = userstat.notes.filter(label='IG').order_by('-date_added').select_related('author',
                                                                                             'author__profile').first()
        userstat.last_note = last_note

    return render(request, 'srbc/users_list_analize.html', {
        "waves": waves,
        "srbc_users": srbc_users_base_stat,
    })


@login_required
def renewal_request_management(request, rrid):
    if not request.user.is_staff:
        return Http404()

    rr = get_object_or_404(RenewalRequest, pk=rrid)
    stat_data = {}

    two_weeks_ago = date.today() - timedelta(days=14)
    # Get Data count total

    stat_data['days_count'] = (date.today() - rr.user.profile.wave.start_date).days + 1

    r = DiaryRecord.objects.filter(user=rr.user, weight__isnull=False).aggregate(data_count=Count(1))
    stat_data['data_count_total'] = r['data_count']
    # Get Data count two weeks
    r = DiaryRecord.objects.filter(user=rr.user, weight__isnull=False) \
        .filter(date__gte=two_weeks_ago) \
        .aggregate(data_count=Coalesce(Count(1), 0))
    stat_data['data_count_2w'] = r['data_count']

    # Get Meals count
    r = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False) \
        .aggregate(data_count=Coalesce(Count(1), V(0)))
    stat_data['meals_count_total'] = r['data_count']
    # Get Meals count two weeks
    r = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False) \
        .filter(date__gte=two_weeks_ago) \
        .aggregate(data_count=Count(1))
    stat_data['meals_count_2w'] = r['data_count']

    # Get FAA Days count
    r = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False, is_meal_reviewed=True) \
        .exclude(faults=0, is_ooc=False) \
        .aggregate(data_count=Count(1))
    stat_data['faa_days_count_total'] = r['data_count']
    # Get FAA Days count two weeks
    r = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False, is_meal_reviewed=True) \
        .filter(date__gte=two_weeks_ago) \
        .exclude(faults=0, is_ooc=False) \
        .aggregate(data_count=Count(1))
    stat_data['faa_days_count_2w'] = r['data_count']

    # Get FAA count
    r1 = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False, is_ooc=False) \
        .aggregate(data_count=Coalesce(Sum('faults'), V(0)))
    r2 = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False, is_ooc=True) \
        .aggregate(data_count=Count(1))

    stat_data['faa_count_total'] = r1['data_count'] + 3 * r2['data_count']

    # Get FAA count two weeks
    r1 = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False, is_ooc=False) \
        .filter(date__gte=two_weeks_ago) \
        .aggregate(data_count=Coalesce(Sum('faults'), V(0)))
    r2 = DiaryRecord.objects.filter(user=rr.user, is_meal_validated=True, is_fake_meals=False, is_ooc=True) \
        .filter(date__gte=two_weeks_ago) \
        .aggregate(data_count=Count(1))

    stat_data['faa_count_2w'] = r1.get('data_count', 0) + 3 * r2.get('data_count', 0)
    # Get notes
    notes = UserNote.objects.filter(user=rr.user).order_by('-date_added')

    header_classes = {
        "TEST": "bg-warning text-warning",
        "OBSERVATION": "bg-info text-info",
        "TREATMENT": "bg-success text-success",
        "DANGER": "bg-danger text-danger",
        "OK": "",
    }

    rr.user.profile.header_class = header_classes.get(rr.user.profile.warning_flag)

    for note in notes:
        note.content = markdownify(note.content)

    # check actions
    return render(request, 'srbc/renewal_request_management.html', {
        "rr": rr,
        "stat_data": stat_data,
        "notes": notes,
    })


@login_required
def facebook_profile_link(request, user_id):
    if not request.user.is_staff:
        return redirect('/')

    requested_user = get_object_or_404(User, pk=user_id)
    facebook_linked = requested_user.social_auth.filter(provider='facebook').first()

    if not facebook_linked:
        raise Http404()

    facebook_data = facebook_linked.extra_data

    graph_url = "https://graph.facebook.com/%s?access_token=%s&fields=link" % (
        facebook_data['id'],
        facebook_data['access_token'],
    )

    api_reponse = requests.get(graph_url)
    api_obj = api_reponse.json()

    if 'link' in api_obj:
        return redirect(api_obj['link'])
    else:
        return HttpResponseBadRequest()


@login_required
def add_regular_analysis(request, user_id):
    if not request.user.is_staff:
        return redirect('/')

    query = User.objects.select_related('profile')
    requested_user = get_object_or_404(query, pk=user_id)

    header_classes = {
        "TEST": "bg-warning text-warning",
        "OBSERVATION": "bg-info text-info",
        "TREATMENT": "bg-success text-success",
        "DANGER": "bg-danger text-danger",
        "OK": "",
    }

    requested_user.profile.header_class = header_classes.get(requested_user.profile.warning_flag)

    profile_serialized = UserProfileSerializer(requested_user)

    last_user_note = UserNote.objects.filter(user_id=user_id, label='IG').order_by('-date_added').first()

    if last_user_note:
        default_data = {
            'adjust_calories': last_user_note.adjust_calories,
            'adjust_protein': last_user_note.adjust_protein,
            'add_fat': last_user_note.add_fat,
            'adjust_fruits': last_user_note.adjust_fruits,
            'adjust_carb_mix_vegs': last_user_note.adjust_carb_mix_vegs,
            'adjust_carb_bread_min': last_user_note.adjust_carb_bread_min,
            'adjust_carb_bread_late': last_user_note.adjust_carb_bread_late,
            'adjust_carb_carb_vegs': last_user_note.adjust_carb_carb_vegs,
            'adjust_carb_sub_breakfast': last_user_note.adjust_carb_sub_breakfast,
            'exclude_lactose': last_user_note.exclude_lactose,
            'restrict_lactose_casein': last_user_note.restrict_lactose_casein,
        }
    else:
        default_data = {}

    try:
        autoanalysis = ProfileTwoWeekStat.objects.filter(user=requested_user).latest('date')
    except ProfileTwoWeekStat.DoesNotExist:
        autoanalysis = None

    if autoanalysis:
        auto_comment = '%s' % autoanalysis.recommendation.comment
    else:
        auto_comment = ''

    default_data['content'] = auto_comment

    profile_data = profile_serialized.data
    profile_data.update({"default_flags": default_data})

    if request.POST.get('action'):
        form = AnalysisAdminForm(request.POST)
        if form.is_valid():
            new_analysis = UserNote(
                author=request.user,
                user=requested_user,
                date_added=timezone.now(),
                content=form.cleaned_data.get('content'),
                is_published=True,
                label='IG'
            )
            new_analysis.save()
            return redirect('/profile/%s/#notes' % requested_user.username)

    else:
        note_initial = {
            "content": auto_comment,
        }

        form = AnalysisAdminForm(initial=note_initial)

    # templates = AnalysisTemplate.objects.filter(is_visible=True)

    return render(request, 'srbc/regular_analysis_add.html', {
        "form": form,
        "ruser": requested_user,
        'profile_serialized': profile_data,

        # "templates": templates,
    })

@login_required
def shortcuts(request):
    if not request.user.is_staff:
        return redirect('/')
    return render(request, 'srbc/shortcuts.html', {
        'bot_name': settings.DJANGO_TELEGRAMBOT['BOTS'][0]['NAME'],
        'base_url': 'https://' + request.get_host(),
    })


@login_required
def add_regular_analysis_old(request, user_id):
    if not request.user.is_staff:
        return redirect('/')

    query = User.objects.select_related('profile', 'profile__wave')
    requested_user = get_object_or_404(query, pk=user_id)

    if request.POST.get('action'):
        form = AnalysisAdminForm(request.POST)
        if form.is_valid():
            new_analysis = UserNote(
                author=request.user,
                user=requested_user,
                date_added=timezone.now(),
                content=form.cleaned_data.get('content'),
                is_published=True,
                label='IG'
            )
            new_analysis.save()
            return redirect('/profile/%s/#notes' % requested_user.username)

    else:
        try:
            autoanalysis = ProfileTwoWeekStat.objects.filter(user=requested_user).latest('date')
        except ProfileTwoWeekStat.DoesNotExist:
            autoanalysis = None

        if autoanalysis:
            auto_comment = '%s\n' % autoanalysis.recommendation.comment
        else:
            auto_comment = ''

        note_initial = {
            "content": auto_comment,
        }

        form = AnalysisAdminForm(initial=note_initial)

    templates = AnalysisTemplate.objects.filter(is_visible=True)

    header_classes = {
        "TEST": "bg-warning text-warning",
        "OBSERVATION": "bg-info text-info",
        "TREATMENT": "bg-success text-success",
        "DANGER": "bg-danger text-danger",
        "OK": "",
    }

    requested_user.profile.header_class = header_classes.get(requested_user.profile.warning_flag)

    return render(request, 'srbc/regular_analisys_add_old.html', {
        "form": form,
        "ruser": requested_user,
        "templates": templates,
    })

@login_required
def sale_prodamus(request):
    if not request.user.is_staff:
        return redirect('/')
    form = ProdamusPaymentForm()
    return render(request, 'srbc/sale_prodamus.html', {
        'form': form
    })