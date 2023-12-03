# -*- coding: utf-8 -*-
import copy
import logging
import math 

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from datetime import time
from django.db.models import Sum, Q

from srbc.models import MealComponent, MealNoticeTemplate, MealProduct, UserNote
from .meal_recommenation import STARCH_BASIC, get_meal_by_time, get_meal_details_by_code, \
    get_meal_recommendation_fulfillment, \
    get_meal_recommendations, START_TIMES
from .meal_component import calculate_component_protein

from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)
LACTOSE_PERCENT = Decimal(4.0)

PROTEIN_BASE = Decimal(24)
FIBER_BASE = Decimal(2)

STARCH_DEDUCTIBLE = Decimal(4.0)

BASE_CONTAINERS = {
    'BREAKFAST': {
        'MEALS': set(),
        'EXTRA': {
            'components': [],
        },
        'FAT': {
            'amount': 0,
            'components': [],
        },
        'FIBER': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'GLUCOSE': {
            'amount': 0,
            'components': [],
        },
        'PROTEIN': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'STARCH': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
    },
    'BRUNCH': {
        'MEALS': set(),
        'EXTRA': {
            'components': [],
        },
        'FAT': {
            'amount': 0,
            'components': [],
        },
        'FIBER': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'GLUCOSE': {
            'amount': 0,
            'components': [],
        },
        'PROTEIN': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'STARCH': {
            'amount': 0,
            'components': [],
        }, },
    'LUNCH': {
        'MEALS': set(),
        'EXTRA': {
            'components': [],
        },
        'FAT': {
            'amount': 0,
            'components': [],
        },
        'FIBER': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'GLUCOSE': {
            'amount': 0,
            'components': [],
        },
        'PROTEIN': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'STARCH': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
    },
    'MERIENDA': {
        'MEALS': set(),
        'EXTRA': {
            'components': [],
        },
        'FAT': {
            'amount': 0,
            'components': [],
        },
        'FIBER': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'GLUCOSE': {
            'amount': 0,
            'components': [],
        },
        'PROTEIN': {
            'amount': 0,
            'components': [],
        },
        'STARCH': {
            'amount': 0,
            'components': [],
        },
    },
    'DINNER': {
        'MEALS': set(),
        'EXTRA': {
            'components': [],
        },
        'FAT': {
            'amount': 0,
            'components': [],
        },
        'FIBER': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'GLUCOSE': {
            'amount': 0,
            'components': [],
        },
        'PROTEIN': {
            'min_percent': Decimal(50),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
        'STARCH': {
            'min_percent': Decimal(0),
            'max_size': 0,
            'required': True,
            'amount': 0,
            'components': [],
        },
    },
    'LATE': {
        'MEALS': set(),
        'EXTRA': {
            'components': [],
        },
        'FAT': {
            'amount': 0,
            'components': [],
        },
        'FIBER': {
            'amount': 0,
            'components': [],
        },
        'GLUCOSE': {
            'amount': 0,
            'components': [],
        },
        'PROTEIN': {
            'amount': 0,
            'components': [],
        },
        'STARCH': {
            'amount': 0,
            'components': [],
        },
    },
}

PLAST_ELEMS = {
    'STARCH': {
        'title': 'сложные углеводы',
        'title_gen': 'сложных углеводов',
    },
    'PROTEIN': {
        'title': 'белок',
        'title_gen': 'белка',
    },
    'FIBER': {
        'title': 'клетчатка',
        'title_gen': 'клетчатки',
    },
}

MEAL_STRUCT_TITLES = {
    'bread': 'хлеба',
    'veg': 'овощей',
    'protein': 'белкового продукта',
    'carb': 'готовых углеводов',
    'rawcarb': 'сухих углеводов',
    'fruit': 'фруктов',
}

EXCESS_PLAST_LIST = ['STARCH']
WAKE_UP_LATE = time(hour=9, minute=30)
BED_TIME_EARLY = time(hour=21, minute=30)


def component_by_plast(meal_component):
    """

    :param meal_component:
    :type meal_component: MealComponent
    :return:
    """
    res = {
        'FAT': 0,
        'FIBER': 0,
        'GLUCOSE': 0,
        'PROTEIN': 0,
        'STARCH': 0,
    }

    product = meal_component.meal_product

    # Get fat from product or component
    # Get protein from product or component
    # Get starch/glucose from product?..
    # Get fiber from product

    res['FIBER'] = (product.fiber_proxy_percent or 0) * meal_component.weight / 100

    # расчет протеина полностью теперь зависит от тега, вынес отдельно, чтобы не затрагивало прошлую логику
    res['PROTEIN'] = calculate_component_protein(meal_component)

    if product.component_type in [MealProduct.TYPE_UNKNOWN, MealProduct.TYPE_MIX]:
        if meal_component.has_custom_nutrition:
            res['FAT'] = (meal_component.details_fat or 0) * meal_component.weight / 100

            if meal_component.details_sugars:
                glucose_percent = meal_component.details_carb
                if not glucose_percent:
                    glucose_percent = product.glucose_proxy_percent

                starch_percent = 0
            else:
                glucose_percent = max(
                    LACTOSE_PERCENT if product.has_tag('LACTOSE') else 0,
                    product.glucose_proxy_percent
                )

                if meal_component.details_carb:
                    starch_percent = max(meal_component.details_carb, glucose_percent) - glucose_percent
                else:
                    starch_percent = 0

            # Углеводная франшиза для белковых продуктов
            if (res['PROTEIN'] > max(res['FAT'], starch_percent) or res['PROTEIN'] >= PROTEIN_BASE / 2) \
                    and starch_percent <= STARCH_DEDUCTIBLE:
                starch_percent = 0

        else:
            res['FAT'] = (product.fat_percent or 0) * meal_component.weight / 100

            if meal_component.details_sugars:
                glucose_percent = product.starch_proxy_percent + product.glucose_proxy_percent
                starch_percent = 0
            else:
                glucose_percent = product.glucose_proxy_percent
                starch_percent = product.starch_proxy_percent

        res['GLUCOSE'] = glucose_percent * meal_component.weight / 100
        res['STARCH'] = starch_percent * meal_component.weight / 100

    else:
        res['FAT'] = (product.fat_percent or 0) * meal_component.weight / 100
        res['GLUCOSE'] = (product.glucose_proxy_percent or 0) * meal_component.weight / 100
        res['STARCH'] = (product.starch_proxy_percent or 0) * meal_component.weight / 100

    return res


def get_meal_containers(diary):
    try:
        recommendations_note = UserNote.objects.filter(
            user_id=diary.user_id,
            is_published=True, label='IG',
            date_added__date__lt=diary.date - timedelta(days=1)
        ).latest('date_added')
    except UserNote.DoesNotExist:
        recommendations_note = None

    meal_recommendation = get_meal_recommendations(
        user_id=diary.user_id, reference_date=diary.date, note=recommendations_note
    )

    logger.info(meal_recommendation)

    # TODO: set containers size (for each meal basing in personal recommendations
    # TODO: process all containers

    components = MealComponent.objects.filter(meal__diary=diary).select_related('meal_product', 'meal').all()
    containers = copy.deepcopy(BASE_CONTAINERS)

    for (meal_key, meal_struct) in meal_recommendation.items():
        for components_template in meal_struct:
            base_component = components_template[0]
            weight = base_component.get('weight') or base_component.get('weight_max')
            ctype = base_component.get('component_type')

            if ctype in ['bread', 'carb', 'rawcarb']:
                if containers.get(meal_key, {}).get('STARCH', {}).get('required'):
                    containers[meal_key]['STARCH']['max_size'] += weight * STARCH_BASIC.get(ctype) / 100

            if ctype in ['veg', 'fruit']:
                if containers.get(meal_key, {}).get('FIBER', {}).get('required'):
                    containers[meal_key]['FIBER']['max_size'] += weight * FIBER_BASE / 100

            if ctype == 'protein':
                if containers.get(meal_key, {}).get('PROTEIN', {}).get('required'):
                    containers[meal_key]['PROTEIN']['max_size'] += weight * PROTEIN_BASE / 100

    for component in components:
        # print(component)

        if component.meal_product is None:
            # print('No product')
            continue

        container_group = get_meal_by_time(component.meal)
        # print(container_group)

        if not container_group:
            # print('No container')
            continue

        containers[container_group]['MEALS'].add(component.meal.start_time)
        component_plast = component_by_plast(component)
        # print(component_plast)

        # print(containers[container_group])
        required_plast = [
            k for (k, v) in containers[container_group].items()
            if k not in ['MEALS', 'EXTRA'] and v.get('required', False)
        ]

        # print(required_plast)

        # extra = all plast are not required
        is_extra = all([k not in required_plast for (k, v) in component_plast.items() if v > 0])
        if is_extra:
            containers[container_group]['EXTRA']['components'].append(component.meal_product.title)

        for (k, v) in component_plast.items():
            if not v:
                continue

            containers[container_group][k]['amount'] += v
            containers[container_group][k]['components'].append(component.meal_product.title)

    anlz_text_codes = []
    plast_total = {
        'PROTEIN': {
            'min': 0,
            'max': 0,
            'total': 0,
        },
        'STARCH': {
            'min': 0,
            'max': 0,
            'total': 0,
        },
        'FIBER': {
            'min': 0,
            'max': 0,
            'total': 0,
        },
    }
    for _m in containers:
        containers[_m]['MEALS'] = [v.strftime("%H:%M") for v in sorted(containers[_m]['MEALS'])]
        container = containers[_m]
        for plast in plast_total:
            container_plast = container.get(plast, {})
            if container_plast.get('required'):
                amount_max = Decimal(container_plast.get('max_size', 0))
                amount_min = amount_max * Decimal(container_plast.get('min_percent', 0) / 100)

                plast_total[plast]['min'] += amount_min
                plast_total[plast]['max'] += amount_max

            plast_total[plast]['total'] += Decimal(container_plast.get('amount', 0))

    # print(plast_total)

    plast_def = [p for p in plast_total if plast_total[p]['total'] < plast_total[p]['min']]
    plast_excess = [p for p in plast_total if
                    plast_total[p]['total'] > plast_total[p]['max'] and p in EXCESS_PLAST_LIST]
    plast_ok = [p for p in plast_total if p not in plast_def + plast_excess]

    if plast_ok:
        anlz_text_codes.append({
            'code': 'DAY_NUTRITION_OK',
            'params': {
                'NUTRITION': plast_ok,
            }
        })

    if plast_def:
        anlz_text_codes.append({
            'code': 'DAY_NUTRITION_DEF',
            'params': {
                'NUTRITION': plast_def,
            }
        })

    if plast_excess:
        anlz_text_codes.append({
            'code': 'DAY_NUTRITION_EXCESS',
            'params': {
                'NUTRITION': plast_excess,
            }
        })

    all_meals_ok = True
    anlz_text_codes_meals = defaultdict(list)

    for _m in containers:
        container = containers[_m]
        plast_status_by_meal = {
            'OK': [],
            'MIS': [],
            'DEF': [],
            'EXC': [],
        }
        for plast in plast_total:
            container_plast = container.get(plast, {})
            amount_actual = Decimal(container_plast.get('amount', 0))

            if container_plast.get('required'):
                amount_max = Decimal(container_plast.get('max_size', 0))
                amount_min = amount_max * Decimal(container_plast.get('min_percent', 0) / 100)
            else:
                amount_min = 0
                amount_max = 0

            if amount_actual == 0 and amount_min > 0:
                plast_status_by_meal['MIS'].append(plast)
            elif amount_actual < amount_min:
                plast_status_by_meal['DEF'].append(plast)
            elif amount_actual > amount_max and plast in EXCESS_PLAST_LIST:
                plast_status_by_meal['EXC'].append(plast)
            elif amount_min > 0:
                plast_status_by_meal['OK'].append(plast)

        if len(plast_status_by_meal['MIS']) or len(plast_status_by_meal['DEF']):
            # В этот промежуток времени необходим полноценный прием пищи (...)."
            anlz_text_codes_meals[_m].append(
                {
                    'code': 'MEAL_NUTRITION_SCHEMA',
                    'params': {
                        'MEAL_SCHEMA': meal_recommendation[_m],
                    }

                }
            )

        if len(plast_status_by_meal['EXC']) or len(plast_status_by_meal['MIS']) or len(plast_status_by_meal['DEF']):
            # В следующий раз возьмите GG грамм XX.
            all_meals_ok = False
            anlz_text_codes_meals[_m].extend([
                {
                    'code': 'MEAL_NUTRITION_SCHEMA_%s' % c,
                    'params': {
                        'NUTRITION': plast_status_by_meal[c],
                    }
                } for c in plast_status_by_meal if len(plast_status_by_meal[c]) and c != 'OK'
            ])

        if recommendations_note:
            non_nutrition_codes = get_meal_recommendation_fulfillment(
                diary=diary,
                recommendations_note=recommendations_note,
                meal_recommendation=meal_recommendation,
                meal_code=_m
            )

            if non_nutrition_codes:
                anlz_text_codes_meals[_m].extend([{'code': c} for c in non_nutrition_codes])

    has_comments = any([len(v) for (k, v) in anlz_text_codes_meals.items()])

    if all_meals_ok and not has_comments:
        anlz_text_codes.append({
            'code': 'MEALS_NUTRITION_OK',
        })
    if not all_meals_ok:
        anlz_text_codes.append({
            'code': 'MEALS_NUTRITION_ADJUST',
        })

    if has_comments:
        anlz_text_codes.append(anlz_text_codes_meals)

    anlz_text = compose_anlz_text(anlz_text_codes)

    # print(anlz_text)
    # logger.info(anlz_text)

    is_reliable = True

    if diary.wake_up_time >= WAKE_UP_LATE:
        is_reliable = False

    if diary.bed_time <= BED_TIME_EARLY and not diary.bed_time_is_next_day:
        is_reliable = False

    return containers, anlz_text_codes, anlz_text, is_reliable


def compose_anlz_text(text_codes, is_sub=False):
    codes = [t.get('code') for t in text_codes if t.get('code')]

    templates = MealNoticeTemplate.objects.filter(code__in=codes, is_active=True).all()
    templates_dict = {t.code: t for t in templates}

    texts = []

    for t in text_codes:
        if t.get('code'):
            if t.get('code') not in templates_dict:
                texts.append(build_meal_text(
                    template=t.get('code'),
                    params=t.get('params', {})
                ))
            else:
                prefix = '- ' if is_sub else ''
                texts.append(build_meal_text(
                    template='%s%s' % (prefix, templates_dict.get(t.get('code')).template),
                    params=t.get('params', {})
                ))
        else:
            for (k, v) in t.items():
                meal_details = get_meal_details_by_code(k)
                if not meal_details:
                    logger.exception('Missing meal: %s' % k)
                    continue

                meal_title = meal_details.get('title')

                if not meal_title:
                    logger.exception('Missing meal title: %s' % k)
                    continue

                if meal_details.get('start') and meal_details.get('end'):
                    meal_time = '%s - %s' % (
                        meal_details.get('start').strftime('%H:%M'),
                        meal_details.get('end').strftime('%H:%M'),
                    )
                elif meal_details.get('start'):
                    meal_time = 'После %s' % (
                        meal_details.get('start').strftime('%H:%M'),
                    )
                else:
                    meal_time = 'До %s' % (
                        meal_details.get('end').strftime('%H:%M'),
                    )
                texts.append(
                    "## %s (%s)\n%s" % (
                        meal_title,
                        meal_time,
                        compose_anlz_text(v, True)
                    )
                )

    glue = '\n' if is_sub else '\n\n'

    return glue.join(texts)


def get_plast_by_code(plast):
    # print(plast, PLAST_ELEMS.get(plast, {}), PLAST_ELEMS.get(plast, {}).get('title_gen'))
    return PLAST_ELEMS.get(plast, {}).get('title_gen')


def build_meal_schema_bit_text(component):
    if component.get('weight_max'):
        return '%s-%sг %s' % (
            component.get('weight_min'),
            component.get('weight_max'),
            MEAL_STRUCT_TITLES.get(component.get('component_type')),
        )
    else:
        return '%sг %s' % (
            component.get('weight'),
            MEAL_STRUCT_TITLES.get(component.get('component_type')),
        )


def build_meal_schema_text(schema):
    schema_texts = []
    for c in schema:
        if isinstance(c, list):
            glue = ' или ' if len(c) <= 2 else ', или '
            schema_texts.append(glue.join([build_meal_schema_bit_text(sc) for sc in c]))
        else:
            schema_texts.append(build_meal_schema_bit_text(c))

    return ', '.join(schema_texts)


def build_meal_text(template, params):
    result = template
    for (k, v) in params.items():

        if 'NUTRITION' == k:
            if len(v) == 1:
                text_value = get_plast_by_code(v[0])
            elif len(v) > 1:
                last_value = get_plast_by_code(v.pop(-1))
                text_value = '%s и %s' % (
                    ', '.join([get_plast_by_code(e) for e in v]),
                    last_value,
                )
            else:
                text_value = '???'
        elif 'MEAL_SCHEMA' == k:
            text_value = build_meal_schema_text(v)
        else:
            text_value = str(v)

        result = result.replace('{%s}' % k, text_value)
    return result

def get_diary_analysis(diary):
    # статусы для конкретного приема пищи
    STATUS_NOT_NEED_NOT_ATE = 'NOT_NEED_NOT_ATE'  # не нужно и не съедено
    STATUS_NOT_NEED_BUT_ATE = 'NOT_NEED_BUT_ATE'  # не нужно, но поедено
    STATUS_NEED_BUT_NOT_ATE = 'NEED_BUT_NOT_ATE'  # нужно, не съедено вообще
    STATUS_NEED_AND_ATE = 'NEED_AND_ATE'  # нужно, съедено
    STATUS_NEED_BUT_ATE_MORE = 'NEED_BUT_ATE_MORE'  # нужно, съедено больше чем нужно
    STATUS_NEED_BUT_ATE_LESS = 'NEED_BUT_ATE_LESS'  # нужно, съедено меньше чем нужно

    # статусы для оценки питания за день
    STATUS_SUCCESS = 'SUCCESS'
    STATUS_INSUFFICIENT = 'INSUFFICIENT'  # недостаток, съедено меньше
    STATUS_EXCESS = 'EXCESS'  # избыток, съедено больше чем нужно
    STATUS_IMBALANCE = 'IMBALANCE'  # скушано, а не надо было

    # TODO вынести в константы в другое место потом
    late_type = 'LATE'

    #FIXME саму структуру функций можно рефакторнуть, но логичней провести рефакторинг исходя из формирования контейнеров 
    # сейчас для LATE в БД другие типы приемов, а в контейнере нет айдишников - лучше менять начиная с этого

    if not diary:
        return None

    containers, _, _, _ = get_meal_containers(diary)

    # сразу получим все компоненты, что были в приеме пищи (чтобы вычислять вес для экстра потом)
    components = MealComponent.objects.filter(meal__diary=diary).select_related('meal_product', 'meal').all()

    # вычисляет данные для столбца EXTRA для переданного приема пищи
    def get_extra_info(data, meal_components, meal_type):
        extra_components = data.get('components', None)
        if extra_components and len(extra_components) > 0:
            extra_components = set(extra_components)
            kcal = 0

            for extra_component in extra_components:
                try:
                    # рассчет кол-ва колорий съеденного

                    # LATE -может быть не одним приемом пищи, а содержать много, один и тот же продукт может быть съеден много раз 
                    # поэтому для него суммируем вес продуктов
                    meal_component = meal_components.filter(meal_product__title=extra_component)[0]
                    if meal_type == late_type:              
                        weight = meal_components.filter(meal_product__title=extra_component).aggregate(total_weight=Sum('weight'))['total_weight']
                    else:
                        weight = meal_component.weight

                    kcal += weight * meal_component.meal_product.calories / 100
                except MealProduct.DoesNotExist:
                    # не должно происходить, на всякий случай
                    capture_exception("Не найден продукт для рассчета съеденных калорий в столбце EXTRA")
                    pass
                except Exception as e:
                    capture_exception(e)
                    pass
            return kcal 
        else:
            return None


    # определяет статус для переданного компонента в конкретный прием пищи
    def get_meal_component_status(data):
        amount = data.get('amount')
        max_size = data.get('max_size', 0)
        min_percent = data.get('min_percent', 0)
        required = data.get('required')

        min_size = Decimal(max_size) * min_percent / 100

        if required:
            if amount == 0:
                return STATUS_NEED_BUT_NOT_ATE
            if amount < min_size:
                return STATUS_NEED_BUT_ATE_LESS
            if amount > max_size:
                return STATUS_NEED_BUT_ATE_MORE

            return STATUS_NEED_AND_ATE
        else:
            if amount > 0:
                return STATUS_NOT_NEED_BUT_ATE

            return STATUS_NOT_NEED_NOT_ATE

    # общий статус дня по переданному компоненту
    def get_day_component_status(containers, name):
        success_count = sum(1 for k, v in containers.items() if
                            v.get(name).get('status') in [STATUS_NEED_AND_ATE, STATUS_NOT_NEED_NOT_ATE])
        insufficient_count = sum(1 for k, v in containers.items() if
                                    v.get(name).get('status') in [STATUS_NEED_BUT_ATE_LESS, STATUS_NEED_BUT_NOT_ATE])
        excess_count = sum(1 for k, v in containers.items() if
                            v.get(name).get('status') in [STATUS_NOT_NEED_BUT_ATE, STATUS_NEED_BUT_ATE_MORE])

        # Недостаточное количество (человек за день недоел продуктов этого типа: 
        # есть недостаточные количества в приемах пищи, нет избыточных количеств этого же типа продуктов в другие приемы пищи)
        if insufficient_count > 0 and excess_count == 0:
            return STATUS_INSUFFICIENT

        # Избыточное количество (человек за день переел продуктов этого типа: есть избыточные количества, нет недостаточных количеств) 
        if excess_count > 0 and insufficient_count == 0:
            return STATUS_EXCESS

        # Дисбаланс по расписанию (возникает, когда есть и избыточные, и недостаточные количества)
        if excess_count > 0 and insufficient_count > 0:
            return STATUS_IMBALANCE

        return STATUS_SUCCESS
    
    # обрабатываем контейнер, определяем статусы каждого компонента и данные о extra
    def create_container_stat(data, components, meal_type):
        result = {
            "MEALS": data.get('MEALS'),
            "EXTRA": data.get('EXTRA'),  # на всякий случай
            "PROTEIN": {
                "status": get_meal_component_status(data.get('PROTEIN'))
            },
            "FIBER": {
                "status": get_meal_component_status(data.get('FIBER'))
            },
            "STARCH": {
                "status": get_meal_component_status(data.get('STARCH'))
            },
        }

        extra_kcal = get_extra_info(data.get('EXTRA'), components, meal_type)

        if extra_kcal:
            result["EXTRA"]["kcal"] = str(extra_kcal)
            result["EXTRA"]["quant_amount"] = str(math.ceil(extra_kcal / 50))
        
        return result



    # сначала "расширяем" контейнеры статусом по нужным компонентам + убираем не нужные
    new_containers = {}

    for k, v in containers.items():
        # осознанно выпиливаем тут LATE из оценки
        # TODO можно сделать через in если будут еще

        if k != late_type:
            # собираем новый контейнер
            new_containers[k] = create_container_stat(v, components.filter(meal__meal_type=k), k)

    day_stat = {
        'PROTEIN': get_day_component_status(new_containers, 'PROTEIN'),
        'FIBER': get_day_component_status(new_containers, 'FIBER'),
        'STARCH': get_day_component_status(new_containers, 'STARCH'),
    }

    #для оценки дневной  статистике не учитывали поздний перекус, 
    # но если он был - его нужно добавить для отображения
    late = containers.get(late_type, None)
    if late and len(late['MEALS']) > 0:

        start_time = next(item.get('start') for item in START_TIMES if item.get('code') == late_type)
        late_components = components.filter(
            Q(meal__start_time__gte=start_time)
            |
            Q(meal__start_time_is_next_day=True)
        )

        new_containers[late_type] = create_container_stat(late, late_components, late_type)

    return {
        'containers': new_containers,
        'day_stat': day_stat
    }