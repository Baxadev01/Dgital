# -*- coding: utf-8 -*-

from datetime import timedelta, datetime, time
from decimal import Decimal

from django.db.models import Q

from srbc.models import DiaryMealFault, DiaryMeal, MealFault, \
    MealComponent
from srbc.utils.meal_containers import get_meal_containers

from .meal_component import calculate_meal_protein


PREBREAKFAST_MIN_FAT_WEIGHT = Decimal(7.0)


def build_meal_fault(fault, diary, meal=None, component=None, comment=None):
    if not comment and fault.comment:
        fault_comment = fault.comment
    else:
        fault_comment = ''

    if component:
        return DiaryMealFault(
            fault=fault,
            diary_record=diary,
            meal_component=component,
            comment=fault_comment
        )
    else:
        return DiaryMealFault(
            fault=fault,
            diary_record=diary,
            meal=meal,
            comment=fault_comment
        )


def is_prebreakfast_ok(meal):
    if meal.components.filter(component_type__in=['fatcarb', ]).count() > 0:
        return True

    if meal.components.filter(component_type__in=['carb', 'rawcarb', 'bread', ]).count() > 0 \
            and meal.details_fat >= PREBREAKFAST_MIN_FAT_WEIGHT:
        return True

    return False


def get_meal_faults(diary):
    meal_faults = MealFault.objects.filter(
        is_active=True
    ).all()

    faults_dict = {f.code: f for f in meal_faults}

    meals = DiaryMeal.objects.filter(diary_id=diary.pk).order_by('start_time_is_next_day', 'start_time').all()

    faults_list = []
    first_alco_time = None

    late_snack_time = datetime.combine(diary.date, time(hour=19, minute=00)) - timedelta(hours=24)
    late_dinner_time = datetime.combine(diary.date, time(hour=18, minute=30)) - timedelta(hours=24)
    late_lunch_time = datetime.combine(diary.date, time(hour=15, minute=0)) - timedelta(hours=24)
    # Надо фиксить время ?
    late_desert_time = datetime.combine(diary.date, time(hour=16, minute=30)) - timedelta(hours=24)
    early_dinner_time = datetime.combine(diary.date, time(hour=16, minute=45)) - timedelta(hours=24)

    pre_alco_break_treshold = timedelta(hours=3)
    pre_sleep_break_treshold = timedelta(hours=3)

    dinner_min_calories = 50
    snack_calories_treshold = 50
    late_carbveg_treshold_calories = 20
    spirit_treshold = 20.0
    late_bombs_weight_treshold = 30
    bomb_min_calories = 400

    prev_snack_time = None
    had_dinner = False
    spirit_day = Decimal(0)

    REDUCED_DINNER_REG_COUNT = 4
    REDUCED_DINNER_REG_DAYS = 14

    for _meal in meals:
        # тут кажется неверным менять на общую проверку "прием ли это пищи"
        if _meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
            prev_snack_time = None
            continue

        if _meal.is_alco:
            if not first_alco_time:
                first_alco_time = _meal.start_timestamp

            spirit_day += _meal.spirit

            _alco_components = _meal.components.filter(meal_product__component_type__in=['alco'])

            _c = MealComponent.objects.filter(component_type='alco', meal=_meal).first()

            if spirit_day > spirit_treshold:
                _f = build_meal_fault(fault=faults_dict['ALCO'], diary=diary, meal=_meal, comment=_c)
                faults_list.append(_f)

            _sparkling_alco = _alco_components.filter(meal_product__tags__system_code='SPARKLING').first()

            if _sparkling_alco is not None:
                _f = build_meal_fault(
                    fault=faults_dict['ALCO_SPARKLING'], diary=diary, meal=_meal, comment=_sparkling_alco
                )

                faults_list.append(_f)

            _sweet_alco = _alco_components.filter(meal_product__is_fast_carbs=True).first()

            if _sweet_alco is not None:
                _f = build_meal_fault(fault=faults_dict['ALCO_SWEET'], diary=diary, meal=_meal, comment=_sweet_alco)
                faults_list.append(_f)

            if _meal.is_substantial(snack_calories_treshold):
                _f = build_meal_fault(fault=faults_dict['ALCO_FOOD'], diary=diary, meal=_meal, comment=_c)
                faults_list.append(_f)
            else:
                if not diary.timespan_calories_check(
                        timestamp_start=_meal.start_timestamp - pre_alco_break_treshold,
                        timestamp_end=_meal.start_timestamp,
                        calories_treshold=snack_calories_treshold
                ):
                    _f = build_meal_fault(fault=faults_dict['ALCO_AFTER_FOOD'], diary=diary, meal=_meal, comment=_c)
                    faults_list.append(_f)

        elif first_alco_time:
            is_alcofood = False

            if _meal.is_substantial(snack_calories_treshold):
                is_alcofood = True
            else:
                if prev_snack_time:
                    if not diary.timespan_calories_check(
                            timestamp_start=prev_snack_time,
                            timestamp_end=_meal.start_timestamp,
                            calories_treshold=snack_calories_treshold
                    ):
                        is_alcofood = True

                else:
                    prev_snack_time = _meal.start_timestamp

            if is_alcofood:
                _f = build_meal_fault(fault=faults_dict['ALCO_FOOD'], diary=diary, meal=_meal)
                faults_list.append(_f)
                if _meal.start_timestamp < late_snack_time:
                    prev_snack_time = None

    prev_meal = None
    prev_substantial_meal = None

    for _meal in meals:
        # Только что проснулись
        # проверить - время перед первым приемом, было ли сладкое в рационе
        if not prev_meal:
            # проверка именно на сон
            if _meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
                prev_meal = _meal
                prev_substantial_meal = _meal
                continue

        if _meal.meal_type == DiaryMeal.MEAL_TYPE_PREBREAKFAST and not is_prebreakfast_ok(_meal):
            _f = build_meal_fault(fault=faults_dict['REC_PREBREAKFAST_FATCARB'], diary=diary, meal=_meal)
            faults_list.append(_f)

        if prev_substantial_meal:
            if prev_substantial_meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
                prev_time = prev_substantial_meal.end_timestamp
            else:
                prev_time = prev_substantial_meal.start_timestamp
        else:
            prev_time = diary.wake_up_timestamp

        # Перерыв после сна
        if not prev_substantial_meal or prev_substantial_meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
            if prev_time > _meal.start_timestamp:
                # TODO: В будущем - помечать рацион как FAKE
                return None, {
                    "status": 'ERROR',
                    "message": "Неверное время пробуждения",
                    "data": None,
                }

            time_elapsed = _meal.start_timestamp - prev_time

            if time_elapsed >= timedelta(hours=2) and _meal.is_substantial(snack_calories_treshold):
                _f = build_meal_fault(fault=faults_dict['LATE_FIRST_MEAL'], diary=diary, meal=_meal)
                faults_list.append(_f)

            if _meal.has_fast_carbs:
                _c = MealComponent.objects.filter(
                    Q(details_sugars=True) | Q(details_carb__isnull=True, meal_product__is_fast_carbs=True),
                    meal=_meal
                ).first()
                _f = build_meal_fault(fault=faults_dict['FASTING_SUGAR_SLEEP'], diary=diary, meal=_meal,
                                      component=_c)
                faults_list.append(_f)
        elif _meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
            check_start = min(late_snack_time, _meal.start_timestamp - pre_sleep_break_treshold)
            if not diary.timespan_calories_check(
                    timestamp_start=check_start,
                    timestamp_end=_meal.start_timestamp,
                    calories_treshold=dinner_min_calories
            ):
                last_snack = None
                for _m in meals:
                    if not _m.is_meal:
                        continue

                    if _m.start_timestamp > _meal.start_timestamp:
                        break

                    last_snack = _m

                _f = build_meal_fault(fault=faults_dict['SLEEP_AFTER_MEAL'], diary=diary, meal=last_snack)
                faults_list.append(_f)

        else:
            if not _meal.has_calories and not _meal.is_alco:
                continue

            time_elapsed = _meal.start_timestamp - prev_time

            # TODO: только до 19-00. После 19-00 - идут отдельно.
            if time_elapsed >= timedelta(hours=3, minutes=30) and _meal.is_substantial(snack_calories_treshold):
                _f = build_meal_fault(fault=faults_dict['MEAL_INTERVAL'], diary=diary, meal=_meal)
                faults_list.append(_f)

            if _meal.has_fast_carbs:
                fasting_sugar = 'FASTING_SUGAR_SLEEP'
                last_meal_is_sweet = False

                for _meal2 in meals:
                    if _meal2.start_timestamp >= _meal.start_timestamp:
                        break

                    if not _meal2.has_calories:
                        continue

                    time_elapsed2 = _meal.start_timestamp - _meal2.start_timestamp

                    if not _meal2.has_fast_carbs:
                        last_meal_is_sweet = False

                    if _meal2.has_fast_carbs and time_elapsed2 > timedelta(minutes=30):
                        last_meal_is_sweet = True

                    if _meal2.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
                        fasting_sugar = 'FASTING_SUGAR_SLEEP'
                        continue

                    if time_elapsed2 >= timedelta(hours=2, minutes=30):
                        fasting_sugar = 'FASTING_SUGAR'
                        continue

                    if timedelta(hours=1) <= time_elapsed2 < timedelta(hours=2, minutes=30) \
                            and fasting_sugar in ['FASTING_SUGAR', 'FASTING_SUGAR_SLEEP']:
                        if _meal2.is_proper_meal:
                            fasting_sugar = False
                        else:
                            fasting_sugar = 'FASTING_SUGAR'
                        continue

                    if time_elapsed2 < timedelta(hours=1) \
                            and fasting_sugar in ['FASTING_SUGAR', 'FASTING_SUGAR_SLEEP']:
                        if _meal2.has_fast_carbs and time_elapsed2 <= timedelta(minutes=30):
                            continue

                        if _meal2.is_proper_meal:
                            fasting_sugar = 'FASTING_SUGAR_FAST'
                        else:
                            fasting_sugar = 'FASTING_SUGAR'
                        continue

                if fasting_sugar or last_meal_is_sweet:
                    _c = MealComponent.objects.filter(
                        Q(details_sugars=True) | Q(details_carb__isnull=True, meal_product__is_fast_carbs=True),
                        meal=_meal
                    ).first()

                    if fasting_sugar:
                        _f = build_meal_fault(
                            fault=faults_dict[fasting_sugar], diary=diary, meal=_meal, component=_c
                        )

                        faults_list.append(_f)

                    if last_meal_is_sweet:
                        _f = build_meal_fault(
                            fault=faults_dict['TWO_SWEET_SCREWED'], diary=diary, meal=_meal, component=_c
                        )
                        faults_list.append(_f)

        if _meal.has_slow_carbs and late_desert_time <= _meal.start_timestamp < late_dinner_time:
            _c = MealComponent.objects.filter(
                component_type__in=[
                    'carb', 'rawcarb',
                ],
                meal=_meal
            ).first()
            _f = build_meal_fault(fault=faults_dict['REC_DINNER_SLOWCARBS'], diary=diary, meal=_meal,
                                  component=_c)
            faults_list.append(_f)

        if _meal.has_fat_carbs and late_lunch_time <= _meal.start_timestamp:
            _c = MealComponent.objects.filter(
                component_type__in=['fatcarb', ],
                meal=_meal
            ).first()
            _f = build_meal_fault(fault=faults_dict['REC_LATE_FATCARBS'], diary=diary, meal=_meal,
                                  component=_c)
            faults_list.append(_f)

        if _meal.start_timestamp >= late_dinner_time \
                and (_meal.has_carbs
                     or
                     _meal.components_weight_by_type(component_types=['carbveg']) > late_carbveg_treshold_calories):
            if _meal.has_carbs:
                _c = MealComponent.objects.filter(
                    component_type__in=[
                        'fruit', 'dfruit', 'desert',
                        'carb', 'rawcarb', 'fatcarb', 'bread',
                    ],
                    meal=_meal
                ).first()
                _f = build_meal_fault(fault=faults_dict['REC_LATE_CARBS'], diary=diary, meal=_meal,
                                      component=_c)
            else:
                _c = MealComponent.objects.filter(
                    component_type__in=[
                        'carbveg',
                    ],
                    meal=_meal
                ).first()
                _f = build_meal_fault(fault=faults_dict['REC_LATE_CARBS'], diary=diary, meal=_meal,
                                      component=_c)

            faults_list.append(_f)

        if _meal.start_timestamp >= late_lunch_time and _meal.has_fast_carbs:
            _c = MealComponent.objects.filter(
                component_type__in=[
                    'desert',
                ],
                meal=_meal
            ).first()
            if _c:
                _f = build_meal_fault(fault=faults_dict['LATE_FASTCARBS_DESERT'], diary=diary, meal=_meal,
                                      component=_c)
                faults_list.append(_f)

        if _meal.start_timestamp >= late_desert_time and _meal.has_fast_carbs:
            _c = MealComponent.objects.filter(
                component_type__in=[
                    'fruit', 'dfruit',
                ],
                meal=_meal
            ).first()
            if _c:
                _f = build_meal_fault(fault=faults_dict['LATE_FASTCARBS_FRUIT'], diary=diary, meal=_meal,
                                      component=_c)
                faults_list.append(_f)

        if _meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP or _meal.has_calories:
            prev_meal = _meal

        if _meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP or _meal.is_substantial(snack_calories_treshold):
            prev_substantial_meal = _meal

    if not diary.timespan_calories_check(
            timestamp_start=diary.bed_timestamp - pre_sleep_break_treshold,
            timestamp_end=diary.bed_timestamp,
            calories_treshold=snack_calories_treshold
    ):

        last_snack = None
        for _m in meals:
            if not _m.is_meal:
                continue

            last_snack = _m

        _f = build_meal_fault(fault=faults_dict['SLEEP_AFTER_MEAL'], diary=diary, meal=last_snack)
        faults_list.append(_f)

    if diary.timespan_calories_check(
            timestamp_start=early_dinner_time,
            timestamp_end=diary.bed_timestamp,
            calories_treshold=dinner_min_calories
    ):
        _f = build_meal_fault(fault=faults_dict['REC_MISSED_DINNER'], diary=diary)
        faults_list.append(_f)

    late_bombs = MealComponent.objects.filter(
        meal__diary=diary
    ).filter(
        Q(
            component_type='fatcarb'
        ) | Q(
            meal_product__is_fast_carbs=True,
            meal_product__calories__gte=bomb_min_calories,
            meal_product__calories__isnull=False
        )
    ).exclude(
        meal__start_time__lte=late_dinner_time.time(), meal__start_time_is_next_day=False
    ).select_related('meal').order_by('meal__start_time_is_next_day', 'meal__start_time', 'id')

    late_bombs_weight = 0
    for component in late_bombs:
        late_bombs_weight += component.weight
        if late_bombs_weight > late_bombs_weight_treshold:
            _f = build_meal_fault(
                fault=faults_dict['LATE_BOMBS'],
                diary=diary,
                meal=component.meal,
                component=component
            )
            faults_list.append(_f)
            break

    containers, _, _, _ = get_meal_containers(diary)

    containers_to_check = []
    containers_to_check.append(containers['DINNER'])
    containers_to_check.append(containers['LATE'])

    if diary.bed_time < time(hour=23, minute=0) and not diary.bed_time_is_next_day:
        containers_to_check.append(containers['MERIENDA'])

    dinner_protein = sum(c['PROTEIN']['amount'] for c in containers_to_check)
    dinner_protein_min = sum(c['PROTEIN'].get('max_size', Decimal(0)) *
                             (c['PROTEIN'].get('min_percent', Decimal(0)) / 100) for c in containers_to_check)

    if dinner_protein < dinner_protein_min:
        # редукция ужина
        _f = build_meal_fault(
            fault=faults_dict['REDUCED_DINNER'],
            diary=diary
        )
        faults_list.append(_f)

        start_day = diary.date - timedelta(days=REDUCED_DINNER_REG_DAYS - 1)

        reduced_count = DiaryMealFault.objects.filter(
            fault=faults_dict['REDUCED_DINNER'],
            diary_record__date__gte=start_day,
            diary_record__date__lt=diary.date,
            diary_record__user=diary.user
        ).count()

        if reduced_count + 1 >= REDUCED_DINNER_REG_COUNT:
            # Систематическая редукция ужина
            _f = build_meal_fault(
                fault=faults_dict['REDUCED_DINNER_REG'],
                diary=diary
            )
            faults_list.append(_f)

    return faults_list, None
