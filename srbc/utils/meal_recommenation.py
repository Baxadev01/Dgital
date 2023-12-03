# -*- coding: utf-8 -*-

import copy
import logging
from collections import defaultdict
from datetime import time, timedelta
from decimal import Decimal
from functools import partial

from django.db.models import F, Q, Sum
from django.utils import timezone

from srbc.models import DiaryMeal, MealComponent, UserNote
from .meal_component import calculate_meal_protein

logger = logging.getLogger(__name__)

BASE_RECOMMENDATIONS = {
    'BREAKFAST': [
        [
            {
                "component_type": "bread",
                "weight_min": 25,
                "weight_max": 50,
            },
        ],
        [
            {
                "component_type": "veg",
                "weight": 100,
            },
        ],
        [
            {
                "component_type": "protein",
                "weight": 100,
            },
        ],
        [
            {
                "component_type": "carb",
                "weight": 100,
            },
            {
                "component_type": "rawcarb",
                "weight": 30,
            },
        ],
    ],
    'BRUNCH': [
        [
            {
                "component_type": "protein",
                "weight": 100,
            },
        ],
        [
            {
                "component_type": "veg",
                "weight": 200,
            },
            {
                "component_type": "fruit",
                "weight": 200,
            },
        ],
    ],
    'LUNCH': [
        [
            {
                "component_type": "bread",
                "weight_min": 25,
                "weight_max": 50,
            },
        ],
        [
            {
                "component_type": "veg",
                "weight": 200,
            },
        ],
        [
            {
                "component_type": "protein",
                "weight": 100,
            },
        ],
    ],
    'MERIENDA': [
        [
            {
                "component_type": "veg",
                "weight": 200,
            },
            {
                "component_type": "fruit",
                "weight": 200,
            },
        ],
    ],
    'DINNER': [
        [
            {
                "component_type": "bread",
                "weight_min": 25,
                "weight_max": 50,
            },
        ],
        [
            {
                "component_type": "veg",
                "weight": 200,
            },
        ],
        [
            {
                "component_type": "protein",
                "weight": 100,
            },
        ],
    ],
}

STARCH_BASIC = {
    'bread': 50,
    'rawcarb': 75,
    'carb': 25,
}

START_TIMES = [
    {
        'start': time(hour=7, minute=0),
        'end': time(hour=10, minute=0),
        'code': 'BREAKFAST',
        'title': 'ЗАВТРАК',
    },
    {
        'start': time(hour=10, minute=0),
        'end': time(hour=12, minute=30),
        'code': 'BRUNCH',
        'title': 'ВТОРОЙ ЗАВТРАК',
    },
    {
        'start': time(hour=12, minute=30),
        'end': time(hour=15, minute=15),
        'code': 'LUNCH',
        'title': 'ОБЕД',
    },
    {
        'start': time(hour=15, minute=15),
        'end': time(hour=16, minute=45),
        'code': 'MERIENDA',
        'title': 'ПОЛДНИК',
    },
    {
        'start': time(hour=16, minute=45),
        'end': time(hour=19, minute=0),
        'code': 'DINNER',
        'title': 'УЖИН',
    },
    {
        'start': time(hour=19, minute=0),
        'code': 'LATE',
        'title': 'ПОЗДНИЙ ПЕРЕКУС',
    },
]

START_TIMES_OVERSLEPT = [
    {
        'start': time(hour=9, minute=30),
        'end': time(hour=12, minute=30),
        'code': 'BREAKFAST_LATE',
        'code_orig': 'BREAKFAST',
        'title': 'ПОЗДНИЙ ЗАВТРАК',

    },
    {
        'start': time(hour=12, minute=30),
        'end': time(hour=15, minute=15),
        'code': 'LUNCH',
        'title': 'ОБЕД',
    },
    {
        'start': time(hour=15, minute=15),
        'end': time(hour=16, minute=45),
        'code': 'MERIENDA',
        'title': 'ПОЛДНИК',
    },
    {
        'start': time(hour=16, minute=45),
        'end': time(hour=19, minute=0),
        'code': 'DINNER',
        'title': 'УЖИН',
    },
    {
        'start': time(hour=19, minute=0),
        'code': 'LATE',
        'title': 'ПОЗДНИЙ ПЕРЕКУС',
    },
]

ADD_FAT_MIN_MEALS = 3
RESTRICT_FRUIT_MAX_SWEET_PER_MEAL = 100
GLUCOSE_MILK = 5
GLUCOSE_FRUIT = 20
FRUIT_BUFFER_SIZE = 30
ALL_COMPONENTS_BUFFER_SIZE = 5
BREAKFAST_TIME_START = time(hour=8, minute=0)
BREAKFAST_TIME_END = time(hour=12, minute=0)
DINNER_TIME_START = time(hour=16, minute=45)
LUNCH_TIME_END = time(hour=15, minute=00)
STARCH_CALC_START_TIME = time(hour=7, minute=0)
EXCLUDE_LACTOSE_PRODUCT_SYSTEM_CODE = 'LACTOSE'
STARCH_PRODUCT_SYSTEM_CODE = 'STARCH'
RESTRICT_LACTOSE_CASEIN_PRODUCT_SYSTEM_CODES = ['LACTOSE', 'CASEIN']

PROTEIN_BASE = Decimal(12)  # на 100гр продукта - 12гр протеина


def get_meal_details_by_code(meal_code):
    for k in START_TIMES:
        if k.get('code') == meal_code:
            return k

    return None


def get_meal_by_time(meal):
    meal_time = meal.start_time
    first_meal = START_TIMES[0]
    last_meal = START_TIMES[-1]

    if meal.start_time_is_next_day:
        return last_meal['code']

    if meal_time < first_meal['start']:
        return None

    for meal_slot in START_TIMES:
        if meal_slot.get('end') and meal_slot.get('end') <= meal_time:
            continue

        if meal_slot['start'] <= meal_time:
            return meal_slot['code']

    return None


def get_time_by_meal_code(meal_code):
    for meal_slot in START_TIMES:
        if meal_slot.get('code') == meal_code:
            return meal_slot.get('start'), meal_slot.get('end')

    return None, None


# TODO: update fruits check
def get_meal_recommendation_fulfillment(diary, recommendations_note, meal_recommendation, meal_code):
    # print(meal_code)
    if not recommendations_note.has_meal_adjustments:
        return []

    meal_times = get_time_by_meal_code(meal_code)

    # Generic queryset
    _c = MealComponent.objects.filter(
        meal__diary=diary
    )

    if meal_times[0] is not None:
        _c = _c.filter(Q(meal__start_time__gte=meal_times[0]) | Q(meal__start_time_is_next_day=True))

    if meal_times[1] is not None:
        _c = _c.filter(meal__start_time__lt=meal_times[1])

    pr_codes = []

    if not meal_times[0]:
        return pr_codes

    if recommendations_note.adjust_carb_mix_vegs:
        # Check vegs proportions
        _c1 = _c.filter(meal_product__component_type='veg').all().aggregate(veg_weight=Sum('weight'))
        veg_weight = _c1['veg_weight'] or 0

        _c2 = _c.filter(meal_product__component_type='carbveg').all().aggregate(veg_weight=Sum('weight'))
        carbveg_weight = _c2['veg_weight'] or 0

        _c3 = _c.filter(meal_product__component_type='fruit').all().aggregate(fr_weight=Sum('weight'))
        fruit_weight = _c3['fr_weight'] or 0

        if carbveg_weight and (carbveg_weight + fruit_weight > veg_weight):
            pr_codes.append('PR_ADJ_FRUITS_CARBVEG')

    if recommendations_note.adjust_fruits != 'NO':
        track_fruits = recommendations_note.adjust_fruits

        # print(track_fruits)

        if track_fruits == 'RESTRICT':
            max_glucose_level = GLUCOSE_FRUIT
        else:
            max_glucose_level = GLUCOSE_MILK

        # Check deserts

        _cs = _c.filter(
            Q(meal_product__glucose_proxy_percent=0) | Q(meal_product__glucose_proxy_percent__gte=max_glucose_level),
            meal_product__is_fast_carbs=True,
        ).exclude(
            Q(details_protein__gt=0) | Q(details_fat__gt=0) | Q(details_carb__gt=0),
            meal_product__component_type='unknown',
            details_sugars=False
        )
        _cs = _cs.all().aggregate(sweet_weight=Sum('weight'))

        # print(_cs)

        if _cs['sweet_weight']:
            if track_fruits == 'RESTRICT':
                pr_codes.append('PR_ADJ_FRUITS_RSTR_SUGAR')
            else:
                pr_codes.append('PR_ADJ_FRUITS_EXCL_SUGAR')

        if track_fruits == 'RESTRICT':
            _cs = _c.filter(
                meal_product__is_fast_carbs=True,
                meal_product__glucose_proxy_percent__gte=GLUCOSE_MILK,
                meal_product__glucose_proxy_percent__lte=GLUCOSE_FRUIT,
            ).exclude(
                Q(details_protein__gt=0) | Q(details_fat__gt=0) | Q(details_carb__gt=0),
                meal_product__component_type='unknown',
                details_sugars=False
            ).all().aggregate(
                sweet_weight=Sum('weight')
            )

            sweet_weight = _cs.get('sweet_weight', 0)

            max_fruit_weight = RESTRICT_FRUIT_MAX_SWEET_PER_MEAL if meal_code in ['BRUNCH', 'MERIENDA'] else 0

            if sweet_weight and sweet_weight > max_fruit_weight:
                pr_codes.append('PR_ADJ_FRUITS_RSTR_FRUITS')

    if recommendations_note.adjust_carb_carb_vegs:
        dinner_carb_vegs = _c.filter(
            meal_product__component_type='carbveg'
        ).filter(
            Q(meal__start_time__gte=LUNCH_TIME_END) | Q(meal__start_time_is_next_day=True),
        ).count()

        if dinner_carb_vegs:
            pr_codes.append('PR_ADJ_CARB_CARBVEGS_VEGS')

        starch_max_dinner = 0
        for block in meal_recommendation.get('DINNER', []):
            component = block[0]
            if component['component_type'] in STARCH_BASIC:
                if component.get('weight', None):
                    weight = component['weight']
                else:
                    weight = component['weight_max']

                starch_max_dinner += weight * STARCH_BASIC.get(component['component_type'], 0)

        starch_actual_dinner = _c.filter(
            meal_product__starch_proxy_percent__gt=0,
            meal_product__tags__system_code__exact=STARCH_PRODUCT_SYSTEM_CODE
        ).filter(
            Q(meal__start_time__gte=LUNCH_TIME_END) | Q(meal__start_time_is_next_day=True)
        ).all().aggregate(total=Sum(F('weight') * F('meal_product__starch_proxy_percent')))['total'] or 0
        # TODO протестировать нужно или нет output_field в SUM. Вроде нет.

        if starch_actual_dinner and starch_actual_dinner > starch_max_dinner:
            pr_codes.append('PR_ADJ_CARB_CARBVEGS_CARB')

    if recommendations_note.exclude_lactose:
        # Рекомендация не выполнена, если в рационе в день есть хотя бы один продукт с тегом "лактоза"
        lactose_exists = _c.filter(meal_product__tags__system_code__exact=EXCLUDE_LACTOSE_PRODUCT_SYSTEM_CODE).exists()
        if lactose_exists:
            pr_codes.append('PR_EXCLUDE_LACT')

    if recommendations_note.restrict_lactose_casein:
        # Рекомендация не выполнена, если в рационе продукты с тегом из списка ["лактоза", "казеин"]
        # есть более чем в одном приеме пищи

        has_dairy = _c.filter(meal_product__tags__system_code__in=RESTRICT_LACTOSE_CASEIN_PRODUCT_SYSTEM_CODES)

        if has_dairy:
            meals_count_w_lactose_or_casein = DiaryMeal.objects.filter(
                diary=diary,
                components__meal_product__tags__system_code__in=RESTRICT_LACTOSE_CASEIN_PRODUCT_SYSTEM_CODES,
                start_time__lt=meal_times[0], start_time_is_next_day=False
            ).distinct().count()
            if meals_count_w_lactose_or_casein > 1:
                pr_codes.append('PR_RESTRICT_LACT_CAS')

    # print(pr_codes)
    return pr_codes


def get_meal_recommendations(user_id, reference_date=None, note=None):
    """ На основании рекомендаций (UserNote) составляет рекомендации по приему пищи для пользователя.

    :param note:
    :param user_id:
    :type user_id: int
    :return: список персонализированных рекомендаций
    :param reference_date
    :type reference_date: date
    :rtype: list(dict)
    """
    recommendations_data = copy.deepcopy(BASE_RECOMMENDATIONS)

    if not reference_date:
        reference_date = timezone.now().date()

    if note is None:
        try:
            note = UserNote.objects.filter(
                user_id=user_id, is_published=True, label='IG', date_added__date__lte=reference_date - timedelta(days=1)
            ).latest('date_added')
        except UserNote.DoesNotExist:
            return recommendations_data

    # === скорректируем на основании замены длинных углеводов для завтрака (DEV-267)
    if ('BREAKFAST' in recommendations_data) and note.adjust_carb_sub_breakfast:
        recommendations_data['BREAKFAST'] = process_adjust_carb_sub_breakfast(recommendations_data['BREAKFAST'])

    functions = []

    # === скорректируем на основании ограничении фруктов
    if note.adjust_fruits in ('RESTRICT', 'EXCLUDE'):
        p_func = partial(process_fruits, adjust_fruits=note.adjust_fruits)
        functions.append(p_func)

    # === скорректируем на основании ограничения потребления хлеба
    if note.adjust_carb_bread_min:
        functions.append(partial(process_bread))

    # === скорректируем вес ВСЕХ навесков по калорийности рациона
    if note.adjust_calories is None:
        note.adjust_calories = 0

    if note.adjust_protein is None:
        note.adjust_protein = 0

    if note.adjust_calories or note.adjust_protein:
        # ВСЕ навески становится становятся k * от базового веса
        # например, если -20, то будет 0.8 * от базового веса

        k_all = (100 + note.adjust_calories) / 100.0
        k_protein = k_all
        if note.adjust_protein:
            k_protein = (100 + note.adjust_protein) / 100.0

        functions.append(partial(process_weight, k_all=k_all, k_protein=k_protein))

    for key, list_value in recommendations_data.items():
        recommendations_data[key] = update_recommendation(list_value, functions)
        if key == 'DINNER' and note.adjust_carb_bread_late:
            # скорректируем на основании ограничения потребления хлеба во время ужина
            recommendations_data[key] = process_bread_late(recommendations_data[key])

    return recommendations_data


def get_recommendation_fulfillment(diary):
    last_user_note = UserNote.objects.filter(
        user_id=diary.user, label='IG',
        date_added__date__lt=diary.date - timedelta(days=1)
    ).order_by('-date_added').first()
    if not last_user_note:
        return 'NA', None

    if not last_user_note.has_meal_adjustments:
        return 'NA', None

    meal_recommendation = get_meal_recommendations(
        user_id=diary.user_id, reference_date=diary.date, note=last_user_note
    )

    logger.info(meal_recommendation)
    logger.info(last_user_note.__dict__)

    meals = DiaryMeal.objects.filter(diary_id=diary.pk).order_by('start_time_is_next_day', 'start_time').all()

    meals_with_fat = 0
    track_fat = False
    track_protein = False
    # track_fruits = False
    track_mix_vegs = last_user_note.adjust_carb_mix_vegs

    carb_vegs_ok = True
    deserts_ok = True
    meals_with_protein = defaultdict(int)
    plan_meals_with_protein = {}
    starch_max = 0
    starch_actual = 0

    # Проверка выполнения рекомендаций по фруктам - навески
    if last_user_note.adjust_fruits == 'NO':
        track_fruits = None
        # max_glucose_level = None
    else:
        track_fruits = last_user_note.adjust_fruits
        if last_user_note.adjust_fruits == 'RESTRICT':
            # max_glucose_level = GLUCOSE_FRUIT
            pass
        else:
            # max_glucose_level = GLUCOSE_MILK
            pass

    if last_user_note.add_fat:
        track_fat = True

    if last_user_note.adjust_protein:
        track_protein = True
        for meal_code in meal_recommendation:
            for block in meal_recommendation[meal_code]:
                component = block[0]
                if component['component_type'] == 'protein':
                    if component['weight']:
                        weight_min = component['weight']
                        weight_max = component['weight']
                    else:
                        weight_min = component['weight_min']
                        weight_max = component['weight_max']

                    plan_meals_with_protein[meal_code] = {
                        'min': weight_min,
                        'max': weight_max,
                    }

    if last_user_note.adjust_carb_bread_min:
        starch_max = 0
        for meal_code in meal_recommendation:
            for block in meal_recommendation[meal_code]:
                component = block[0]
                if component['component_type'] in STARCH_BASIC:
                    if component.get('weight', None):
                        weight = component['weight']
                    else:
                        weight = component['weight_max']

                    starch_max += weight * STARCH_BASIC.get(component['component_type'], 0)

        starch_actual = MealComponent.objects.filter(
            meal_product__starch_proxy_percent__gt=0,
            meal_product__tags__system_code__exact=STARCH_PRODUCT_SYSTEM_CODE,
            meal__diary=diary
        ).exclude(
            meal__start_time__lt=STARCH_CALC_START_TIME,
            meal__start_time_is_next_day=False
        ).all().aggregate(total=Sum(F('weight') * F('meal_product__starch_proxy_percent')))

        starch_actual = starch_actual['total'] or 0

        starch_actual_prods = MealComponent.objects.filter(
            meal_product__starch_proxy_percent__gt=0,
            meal_product__tags__system_code__exact=STARCH_PRODUCT_SYSTEM_CODE,
            meal__diary=diary
        ).exclude(
            meal__start_time__lt=STARCH_CALC_START_TIME,
            meal__start_time_is_next_day=False
        ).values_list('meal_product_id', 'meal_product__starch_proxy_percent', 'meal_product__title').all()

        logger.info("Starch: %s / %s" % (starch_actual, starch_max,))
        logger.info(list(starch_actual_prods))

    for _meal in meals:
        meal_type = _meal.meal_type

        if not _meal.is_meal:
            continue

        if track_protein:
            meals_with_protein[_meal.meal_type] += calculate_meal_protein(_meal) * 100 / PROTEIN_BASE

        if track_fat:
            _c = MealComponent.objects.filter(
                component_type__in=['fatcarb', 'fat'],
                meal=_meal
            ).first()

            if _c:
                meals_with_fat += 1

        if track_mix_vegs and carb_vegs_ok:
            _c = MealComponent.objects.filter(
                meal_product__component_type='veg',
                meal=_meal
            ).all().aggregate(veg_weight=Sum('weight'))

            veg_weight = _c['veg_weight'] or ALL_COMPONENTS_BUFFER_SIZE

            _c = MealComponent.objects.filter(
                meal_product__component_type__in=['carbveg'],
                meal=_meal
            ).all().aggregate(veg_weight=Sum('weight'))

            carbveg_weight = _c['veg_weight'] or 0

            _c = MealComponent.objects.filter(
                meal_product__component_type__in=['fruit'],
                meal=_meal
            ).all().aggregate(fr_weight=Sum('weight'))

            fruit_weight = _c['fr_weight'] or 0

            # print(_meal.start_time, carbveg_weight, fruit_weight, veg_weight)

            if carbveg_weight and (carbveg_weight + fruit_weight > veg_weight):
                carb_vegs_ok = False

        if track_fruits and deserts_ok:
            _c = MealComponent.objects.filter(
                meal_product__is_fast_carbs=True,
                meal_product__glucose_proxy_percent__gte=GLUCOSE_MILK,
                meal_product__glucose_proxy_percent__lte=GLUCOSE_FRUIT,
                meal=_meal
            ).exclude(
                Q(details_protein__gt=0) | Q(details_fat__gt=0) | Q(details_carb__gt=0),
                meal_product__component_type='unknown',
                details_sugars=False
            ).all().aggregate(
                sweet_weight=Sum('weight')
            )

            _c_l = MealComponent.objects.filter(
                meal_product__is_fast_carbs=True,
                meal_product__glucose_proxy_percent__gte=GLUCOSE_MILK,
                meal_product__glucose_proxy_percent__lte=GLUCOSE_FRUIT,
                meal=_meal
            ).exclude(
                Q(details_protein__gt=0) | Q(details_fat__gt=0) | Q(details_carb__gt=0),
                meal_product__component_type='unknown',
                details_sugars=False
            ).all()

            # print([(i.meal_product, i.weight) for i in _c_l])

            fruit_restrict = RESTRICT_FRUIT_MAX_SWEET_PER_MEAL if track_fruits == 'RESTRICT' else FRUIT_BUFFER_SIZE

            # max_fruit_weight = fruit_restrict if meal_type in [
            #     DiaryMeal.MEAL_TYPE_BRUNCH, DiaryMeal.MEAL_TYPE_MERIENDA] else ALL_COMPONENTS_BUFFER_SIZE
            # print(max_fruit_weight)

            # убрали проверку на типы приемы пищи для ограничения фруктов
            max_fruit_weight = fruit_restrict

            if _c['sweet_weight'] and _c['sweet_weight'] > max_fruit_weight:
                # print("_c['sweet_weight'] and _c['sweet_weight'] > max_fruit_weight")
                deserts_ok = False

        if track_fruits and deserts_ok:
            _c = MealComponent.objects.filter(
                Q(meal_product__glucose_proxy_percent__gt=GLUCOSE_FRUIT) | Q(meal_product__glucose_proxy_percent=0),
                meal_product__is_fast_carbs=True,
                meal=_meal
            ).exclude(
                Q(details_protein__gt=0) | Q(details_fat__gt=0) | Q(details_carb__gt=0),
                meal_product__component_type='unknown',
                details_sugars=False
            ).all().aggregate(
                sweet_weight=Sum('weight')
            )

            _c_l = MealComponent.objects.filter(
                Q(meal_product__glucose_proxy_percent__gt=GLUCOSE_FRUIT) | Q(meal_product__glucose_proxy_percent=0),
                meal_product__is_fast_carbs=True,
                meal=_meal
            ).exclude(
                Q(details_protein__gt=0) | Q(details_fat__gt=0) | Q(details_carb__gt=0),
                meal_product__component_type='unknown',
                details_sugars=False
            ).all()

            # print([(i.meal_product, i.weight) for i in _c_l])

            if _c['sweet_weight'] and _c['sweet_weight'] > 0:
                # print("_c['sweet_weight'] > 0")
                deserts_ok = False

    faults = []

    if last_user_note.adjust_calories:
        pass

    if last_user_note.adjust_protein:
        for meal_code in plan_meals_with_protein:
            if meal_code in meals_with_protein \
                    and meals_with_protein[meal_code] < plan_meals_with_protein[meal_code]['min']:
                print('Protein (%s): %s < %s' % (
                    meal_code,
                    meals_with_protein[meal_code],
                    plan_meals_with_protein[meal_code]['min'],
                ))
                faults.append('adjust_protein')
                break

    if last_user_note.add_fat:
        if meals_with_fat < ADD_FAT_MIN_MEALS:
            pass
            # faults.append('add_fat')

    if last_user_note.adjust_fruits in ['RESTRICT', 'EXCLUDE']:
        if not deserts_ok:
            faults.append('adjust_fruits_sugar')

    if last_user_note.adjust_carb_mix_vegs:
        if not carb_vegs_ok:
            faults.append('adjust_carb_mix_vegs')

    if last_user_note.adjust_carb_bread_min:
        if starch_actual > starch_max:
            faults.append('adjust_carb_bread_min')

    if last_user_note.adjust_carb_bread_late:
        dinner_carbs = MealComponent.objects.filter(
            meal_product__starch_proxy_percent__gt=0,
            meal_product__tags__system_code__exact=STARCH_PRODUCT_SYSTEM_CODE
        ).filter(
            Q(meal__start_time__gte=DINNER_TIME_START) | Q(meal__start_time_is_next_day=True),
            meal__diary=diary
        ).aggregate(total=Sum('weight'))['total'] or 0

        if dinner_carbs > ALL_COMPONENTS_BUFFER_SIZE:
            faults.append('adjust_carb_bread_late')

    if last_user_note.adjust_carb_carb_vegs:
        dinner_carb_vegs = MealComponent.objects.filter(
            meal_product__component_type='carbveg'
        ).filter(
            Q(meal__start_time__gte=LUNCH_TIME_END) | Q(meal__start_time_is_next_day=True),
            meal__diary=diary
        ).aggregate(total=Sum('weight'))['total'] or 0

        if dinner_carb_vegs > ALL_COMPONENTS_BUFFER_SIZE:
            faults.append('adjust_carb_carb_vegs_carbveg')

        starch_max_dinner = 0
        for block in meal_recommendation.get('DINNER', []):
            component = block[0]
            if component['component_type'] in STARCH_BASIC:
                if component.get('weight', None):
                    weight = component['weight']
                else:
                    weight = component['weight_max']

                starch_max_dinner += weight * STARCH_BASIC.get(component['component_type'], 0)

        starch_actual_dinner = MealComponent.objects.filter(
            meal_product__starch_proxy_percent__gt=0,
            meal_product__tags__system_code__exact=STARCH_PRODUCT_SYSTEM_CODE
        ).filter(
            Q(meal__start_time__gte=LUNCH_TIME_END) | Q(meal__start_time_is_next_day=True),
            meal__diary=diary
        ).all().aggregate(total=Sum(F('weight') * F('meal_product__starch_proxy_percent')))['total'] or 0
        # TODO протестировать нужно или нет output_field в SUM. Вроде нет.

        starch_max_dinner = max(starch_max_dinner, STARCH_BASIC['rawcarb'] * ALL_COMPONENTS_BUFFER_SIZE)
        if starch_actual_dinner and starch_actual_dinner > starch_max_dinner:
            faults.append('adjust_carb_carb_vegs_carb')

    if last_user_note.adjust_carb_sub_breakfast:
        starch_max_lunch = 0
        for block in meal_recommendation.get('LUNCH', []):
            component = block[0]
            if component['component_type'] in STARCH_BASIC:
                if component.get('weight', None):
                    weight = component['weight']
                else:
                    weight = component['weight_max']

                starch_max_lunch += weight * STARCH_BASIC.get(component['component_type'], 0)

        starch_actual_breakfast = MealComponent.objects.filter(
            meal_product__starch_proxy_percent__gt=0,
            meal_product__tags__system_code__exact=STARCH_PRODUCT_SYSTEM_CODE,
            weight__gt=ALL_COMPONENTS_BUFFER_SIZE
        ).filter(
            meal__start_time__gte=BREAKFAST_TIME_START,
            meal__start_time__lte=BREAKFAST_TIME_END,
            meal__start_time_is_next_day=False,
            meal__diary=diary
        ).all().aggregate(total=Sum(F('weight') * F('meal_product__starch_proxy_percent')))['total'] or 0
        # TODO протестировать нужно или нет output_field в SUM. Вроде нет.

        starch_actual_breakfast = starch_actual_breakfast or 0

        if starch_actual_breakfast > starch_max_lunch:
            faults.append('adjust_carb_sub_breakfast')

    if last_user_note.exclude_lactose:
        # Рекомендация не выполнена, если в рационе в день есть хотя бы один продукт с тегом "лактоза"
        # TODO: много раз в один прием пищи по 5 г - не отлавливается
        #####################################################
        # биохимический смысл:
        # рекомендация для капучинофилов с инсулинорезистентностью.
        # Им реально никогда не надо лактозы
        #####################################################
        lactose_exists = MealComponent.objects.filter(
            meal__diary=diary,
            meal_product__tags__system_code__exact=EXCLUDE_LACTOSE_PRODUCT_SYSTEM_CODE,
            weight__gt=ALL_COMPONENTS_BUFFER_SIZE
        ).exists()
        if lactose_exists:
            faults.append('exclude_lactose')

    if last_user_note.restrict_lactose_casein:
        # Рекомендация не выполнена, если в рационе продукты с тегом из списка ["лактоза", "казеин"]
        # есть более чем в одном приеме пищи
        #####################################################
        # биохимический смысл:
        # рекомендация для сыроедов, которые едят молочку во все приемы пищи,
        # страдая от недостатка аминокислот на фоне избытка питательных
        # веществ тогда, когда они не нужны
        #####################################################
        components_w_lactose_or_casein = MealComponent.objects.filter(
            meal__diary=diary,
            meal_product__tags__system_code__in=RESTRICT_LACTOSE_CASEIN_PRODUCT_SYSTEM_CODES,
            weight__gt=ALL_COMPONENTS_BUFFER_SIZE
        ).distinct('meal_id').count()

        if components_w_lactose_or_casein > 1:
            components_w_lactose_or_casein_list = MealComponent.objects.filter(
                meal__diary=diary,
                meal_product__tags__system_code__in=RESTRICT_LACTOSE_CASEIN_PRODUCT_SYSTEM_CODES,
                weight__gt=ALL_COMPONENTS_BUFFER_SIZE
            ).distinct('meal_id').all()

            # print([c.meal_product for c in components_w_lactose_or_casein_list])
            faults.append('restrict_lactose_casein')

    if faults:
        return 'F', faults
    else:
        return 'OK', None


def update_recommendation(data, functions):
    """ Применить изменения к базовым рекомендациям

    :param data: данные рекомендаций
    :type data: list
    :param functions: какие изменения (функции) необходимо применить
    :type: list
    :rtype: list
    """
    for func in functions:
        data = apply_func(data, func)

    return data


def apply_func(data, func):
    func.keywords['data'] = data
    return func()


def process_weight(k_all, k_protein, data):
    """ Обрабатывает изменения веса продуктов на основании рекомендации

    :param k_all:
    :type k_all: float
    :param k_protein:
    :type k_protein: float
    :param data:
    :type data: list
    :rtype: list
    """
    result = []
    for _data in data:
        _result = []
        for d in _data:
            if d['component_type'] == 'protein':
                _result.append(_change_weight(k_protein, d))
            else:
                _result.append(_change_weight(k_all, d))

        result.append(_result)

    return result


def _change_weight(k, data):
    """ Изменяет weight, weight_min, weight_max в data

    :param k:
    :type k: float
    :param data:
    :type data: dict
    :rtype: dict
    """
    for key in ('weight_min', 'weight_max', 'weight'):
        if key in data:
            data[key] = round(data[key] * k * 0.2) * 5

    return data


def process_fruits(adjust_fruits, data):
    """ Обрабатывает изменения фруктов на основании рекомендации

    :param adjust_fruits:
    :type adjust_fruits: str
    :param data:
    :type data: list
    :rtype: list
    """
    if adjust_fruits == 'RESTRICT':
        # RESTRICT - берем минмальное количество фрукта (fruit) или сухофрукта (dfruit)
        result = []
        for _data in data:
            _result = []
            for d in _data:
                # _result.append(_halve_component(component_types=['fruit', 'dfruit'], data=d))
                data_adj = _restrict_component(component_types=['fruit'], data=d, weight_min=100)
                data_adj = _restrict_component(component_types=['dfruit'], data=data_adj, weight_min=30)
                _result.append(data_adj)

            result.append(_result)

        return result

    elif adjust_fruits == 'EXCLUDE':
        return _exclude_fruits(data)


def _restrict_component(component_types, data, weight_min=None, weight_max=None):
    """ У определенных component_types оставляем только минимальное значение веса в рекомендации.

    :param component_types:
    :type component_types: list
    :param data:
    :type data: dict
    :rtype: dict
    """
    if data['component_type'] in component_types:
        data.pop('weight_min', None)
        data.pop('weight_max', None)
        data.pop('weight', None)

        if weight_min and weight_max:
            data['weight_min'] = weight_min
            data['weight_max'] = weight_max
        else:
            data['weight'] = weight_min

    return data


def _halve_component(component_types, data):
    """ У определенных component_types уполовиниваем навески.

    :param component_types:
    :type component_types: list
    :param data:
    :type data: dict
    :rtype: dict
    """
    if data['component_type'] in component_types:
        if 'weight_min' in data:
            # Оставляем только weight_min, а остальное выкидываем. В связи с этим, вес указываем как `weight`
            data['weight_min'] = round(data['weight_min'] / 2)
            data['weight_max'] = round(data['weight_max'] / 2)
        elif 'weight' in data:
            # оставляем только weight и на всякий случай выкидываем остальное (хотя их не должно быть)
            data['weight'] = round(data['weight'] / 2)
        else:
            raise NotImplementedError

    return data


def _exclude_fruits(data):
    """
    EXCLUDE -> фрукты меняем на овощи, сухофрукты убираем (если овощи есть в списке, то фрукты просто выкидываем)

    :param data:
    :type data: list
    :rtype: list
    """
    if "'veg'" in str(data) or '"veg"' in str(data):
        # овощи есть в списке => фрукты выкидываем из списка
        result = []
        for _data in data:
            _result = []
            for d in _data:
                if d['component_type'] not in ('fruit', 'dfruit'):
                    _result.append(d)

            result.append(_result)

        return result
    else:
        # заменяем фрукты на овощи, сухофрукты убираем
        result = []
        for _data in data:
            _result = []
            for d in _data:
                if d['component_type'] == 'fruit':
                    d['component_type'] = 'veg'
                    _result.append(d)
                elif d['component_type'] != 'dfruit':
                    _result.append(d)

            result.append(_result)

        return result


def process_bread(data):
    """ Ограничивает рекомендацию по хлебу

    :param data:
    :type data: list
    :rtype: list
    """
    result = []
    for _data in data:
        _result = []
        for d in _data:
            _result.append(_restrict_component(component_types=['bread'], data=d, weight_min=25, weight_max=30))

        result.append(_result)

    return result


def process_bread_late(data):
    """ Убирает потребление хлеба

    :param data:
    :type data: list
    :rtype: list
    """
    result = []
    for _data in data:
        _result = []
        for d in _data:
            if d['component_type'] != 'bread':
                _result.append(d)

        if _result:
            result.append(_result)

    return result


def process_adjust_carb_sub_breakfast(data):
    """ Определяет замену длинных углеводов для завтрака:
            carb, rawcarb - убрать,  veg - увеличить на величину убранных CARB

    :param data:
    :type data: list
    :rtype: list
    """
    veg_addition_min = 0
    veg_addition_max = 0
    veg_node = None
    result = []
    for _data in data:
        _result = []
        for d in _data:
            if d['component_type'] in ('carb', 'rawcarb'):
                if 'weight_min' in d:
                    if d['component_type'] == 'carb':
                        veg_addition_min = d['weight_min']
                        veg_addition_max = d['weight_max']
                elif 'weight' in d:
                    if d['component_type'] == 'carb':
                        veg_addition_min = d['weight']
                        veg_addition_max = d['weight']
            else:
                _result.append(d)
                if d['component_type'] == 'veg':
                    veg_node = d

        if _result:
            result.append(_result)

    if veg_node:
        if 'weight_min' in veg_node:
            veg_node['weight_min'] += veg_addition_min
            veg_node['weight_max'] += veg_addition_max
        elif 'weight' in veg_node:
            if veg_addition_min != veg_addition_max:
                veg_node['weight'] += round((veg_addition_min + veg_addition_max) / 2)
            else:
                veg_node['weight'] += veg_addition_min
    else:
        veg_node = {"component_type": "veg"}
        if veg_addition_min != veg_addition_max:
            veg_node['weight_min'] = veg_addition_min
            veg_node['weight_max'] = veg_addition_max
        else:
            veg_node['weight'] = veg_addition_min
        result.append(veg_node)

    return result
