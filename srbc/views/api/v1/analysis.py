from datetime import datetime, timedelta, date, time
from collections import defaultdict
from decimal import Decimal
from operator import itemgetter

import pandas as pd


from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.aggregates import Count, Sum
from django.db.models import F
from rest_framework_tracking.mixins import LoggingMixin

from srbc.serializers.general import MealFaultsSerializer, UserNoteSerializer
from srbc.utils.permissions import HasStaffPermission
from srbc.utils.diary import calculate_user_stat
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from srbc.models import DiaryMeal, DiaryMealFault, DiaryRecord, MealComponent, MealFault, \
    MealProductTag, User, UserNote


class RegularAnalysis(LoggingMixin, APIView):
    permission_classes = (HasStaffPermission, )

    @swagger_auto_schema(
        **swagger_docs['GET /v1/analysis/{user_id}/regular/']
    )
    def get(self, request, user_id):
        """
        Анализ пользователя
        
        Получение общей статистики пользователя за промежуток времени (по умолчанию за последние две недели)
        """

        try:
            requested_user = User.objects.select_related('profile').get(pk=user_id)
        except User.DoesNotExist:
            return Response({})

        last_user_note = UserNote.objects.filter(user_id=user_id, label='IG').order_by('-date_added').first()

        # если не задана дата , то по умолчанию делаем интервал в 2 недели
        if request.query_params.get('start_date'):
            interval_start = datetime.strptime(request.query_params.get('start_date'), '%Y-%m-%d')

            # TODO оставить, для тестов
            # interval_start = datetime.strptime("11/15/19", '%m/%d/%y')
        else:
            now = datetime.combine(date.today(), time(hour=12, minute=0))
            interval_start = now - timedelta(days=now.date().weekday(), weeks=2)

        if request.query_params.get('end_date'):
            interval_end = datetime.strptime(request.query_params.get('end_date'), '%Y-%m-%d')
        else:
            interval_end = interval_start + timedelta(days=13)

        # TODO оставить, для тестов
        # interval_end = interval_start + timedelta(days=13)

        interval_start = interval_start.date()
        interval_end = interval_end.date()

        notes = UserNote.objects.filter(user_id=user_id, label='IG').order_by('-date_added')

        recommendation_faults = {
            'add_fat': {"faults": ['add_fat'], 'title': 'Добавить жиров'},
            'adjust_calories': {"faults": [], 'title': 'Корректировка калорийности рациона'},
            'adjust_carb_bread_late': {"faults": ['adjust_carb_bread_late'], 'title': 'Убрать хлеб из ужина'},
            'adjust_carb_bread_min': {"faults": ['adjust_carb_bread_min'], 'title': 'Минимизировать хлеб'},
            'adjust_carb_carb_vegs': {"faults": ['adjust_carb_carb_vegs_carbveg', 'adjust_carb_carb_vegs_carb'],
                                      'title': 'Исключить запасающие овощи после обеда'},
            'adjust_fruits': {"faults": ['adjust_fruits_sugar'], 'title': 'Ограничение фруктов'},
            'adjust_protein': {"faults": ['adjust_protein'], 'title': 'Корректировка белка в рационе'},
            'adjust_carb_sub_breakfast': {"faults": ['adjust_carb_sub_breakfast'], 'title': 'Замена длинных углеводов на овощи(завтрак посхеме обеда)'},
            'exclude_lactose': {"faults": ['exclude_lactose'], 'title': 'Исключить лактозу'},
            'restrict_lactose_casein': {"faults": ['restrict_lactose_casein'], 'title': 'Ограничить казеин и лактозу'},
            'adjust_carb_mix_vegs': {"faults": ['adjust_carb_mix_vegs'], 'title': 'Смешивать овощи'}
        }

        days_count = (interval_end - interval_start).days + 1
        empty_set = [None for _ in range(days_count)]

        # делаем объект дял списка рекоммендаций за период
        pers_req = {}

        # будут только уникальные записи
        given_recommendations = set()

        for item in recommendation_faults:
            pers_req[item] = [None for _ in range(days_count)]

        end_index = days_count
        for note in notes:
            note_date = note.date_added.date()

            # если добавлена после искомого периода, то скипаем
            if note_date > interval_end:
                continue

            # если добавлена до искомой даты, то заполняем начало отрезка и прерываем
            elif note_date <= interval_start:
                start_index = 0

            # рекоммендация во время искомого отрезка - заполняем от нее до следующей
            else:
                start_index = (note_date - interval_start).days

            # если дошли сюда - у нас выставлены индексы для заполнения
            for item in recommendation_faults:
                value = getattr(note, item)

                # проверяем была ли рекоммендация
                if not(value == 'NO' or not value):
                    # была, значит добавляем
                    given_recommendations.add(item)

                for index in range(start_index, end_index):
                    pers_req[item][index] = value

            # прервыраем цикл, если все прошли
            if(start_index == 0):
                break
            else:
                end_index = start_index

        # итоговая стата, содержит список только рекомендованных за данный период вещей
        # и общую статистику за период
        pers_req_stat = {
            "general": {
                "days": 0,
                "success_days": 0
            },
            "recommendations": [{'code': item, 'stat': [], 'title': recommendation_faults[item].get(
                'title')} for item in given_recommendations]
        }

        doc_notes = UserNote.objects.filter(
            user_id=user_id,
            label='DOC',
            date_added__gte=interval_start,
            date_added__lte=interval_end
        ).order_by('-date_added')

        diaries = DiaryRecord.objects.filter(
            user=requested_user,
            date__gte=interval_start,
            date__lte=interval_end
        ).order_by('date').prefetch_related(
            'faults_list', 'faults_list__fault',
            'meals_data__components',
            'meals_data__components__meal_product'
        )

        diaries_dict = {d.date: d for d in diaries}

        dates_list = pd.date_range(interval_start, interval_end).tolist()
        dates_list = [d.date() for d in dates_list]
        meal_dates_list = [d - timedelta(days=1) for d in dates_list]

        last_weight_rec = DiaryRecord.objects.filter(
            user=requested_user, date__lte=interval_start, weight__isnull=False
        ).values('weight').order_by('-date').first()

        if last_weight_rec:
            last_weight = last_weight_rec.get('weight')
        else:
            last_weight = None

        water_required_per_kilo = Decimal(0.04)
        water_stat = []
        water_avg = []
        meal_class_days = []
        steps_filled_days = []
        meal_filled_days = []
        pers_req_flags = []
        hunger_stat = []

        for _date in dates_list:
            diary = diaries_dict.get(_date)

            if not diary:
                meal_class_days.append('miss')
            else:
                meal_class_days.append(diary.meal_status.lower())

            if diary and diary.steps:
                steps_filled_days.append(diary.steps)

            if diary and (diary.pers_rec_flag == 'F' or diary.pers_rec_flag == 'OK'):
                meal_filled_days.append({
                    'pers_req_flag': diary.pers_rec_flag,
                    'meals': diary.meals
                })

            if not diary:
                pers_req_flags.append('NULL')
                for item in pers_req_stat.get('recommendations'):
                    item['stat'].append('NULL')

                hunger_stat.append({
                    'date': _date,
                    'hunger': 'NA',
                })

            else:
                if diary.meal_status in ["FAKE", "DONE"]:
                    pers_req_stat.get('general')['days'] += 1

                if diary.meal_status == "DONE":
                    if (diary.pers_rec_flag != 'F'):
                        pers_req_stat.get('general')['success_days'] += 1

                pers_req_flags.append(diary.pers_rec_flag)

                for item in pers_req_stat.get('recommendations'):

                    if diary.pers_rec_flag == 'F' or diary.pers_rec_flag == 'OK':
                        index = (_date - interval_start).days

                        # проверяем была ли рекоммендация на этот день
                        value = pers_req[item.get('code')][index]
                        if not(value == 'NO' or not value):
                            # провреяем был ли фейл для данной рекоммендации
                            if diary.pers_req_faults and diary.pers_req_faults != '{}':
                                # надо понять есть ли пересечения
                                was_fault = len(
                                    list(
                                        set(diary.pers_req_faults) &
                                        set(recommendation_faults[item.get('code')].get('faults'))))
                                if was_fault:
                                    item['stat'].append('F')
                                else:
                                    item['stat'].append('OK')
                            else:
                                item['stat'].append('OK')
                        else:
                            item['stat'].append('miss')  # не было на этот день данной рекоммендации
                    else:
                        item['stat'].append(diary.pers_rec_flag)

                hunger_stat.append({
                    'date': _date,
                    'hunger': diary.meals_data.filter(meal_type=DiaryMeal.MEAL_TYPE_HUNGER).count(),
                })

            if not diary or not diary.water_consumed:
                water_stat.append({
                    'date': _date,
                    'water': None,
                    'water_per_kilo': None,
                    'water_percentage': None,
                    'water_flag': 'NO',
                })
                continue

            if diary.weight:
                last_weight = diary.weight

            if not last_weight:
                water_stat.append({
                    'date': diary.date,
                    'water': diary.water_consumed,
                    'water_per_kilo': None,
                    'water_percentage': None,
                    'water_flag': 'NO',
                })
                continue

            water_per_kilo = diary.water_consumed / last_weight
            water_percentage = int(water_per_kilo / water_required_per_kilo * 100)
            water_avg.append(min(water_per_kilo, water_required_per_kilo))

            water_stat.append({
                'date': diary.date,
                'water': diary.water_consumed,
                'water_per_kilo': water_per_kilo * 1000,
                'water_percentage': water_percentage,
                'water_flag': 'OK' if water_percentage >= 100 else 'DRY',
            })

        water_stat = sorted(water_stat, key=lambda x: x.get('date'))
        water_stat_avg = sum(water_avg) / len(water_avg) * 1000 if len(water_avg) else None

        water_dry_days = [w for w in water_avg if w < water_required_per_kilo]

        lazy_days_steps = [s for s in steps_filled_days if s < 10000]

        steps_stat = {
            'filled_days': len(steps_filled_days),
            'active_days': sum(1 for d in steps_filled_days if d >= 10000),
            'lazy_days_avg_percent': sum(lazy_days_steps) / len(lazy_days_steps) / 10000 * 100
            if len(lazy_days_steps) else None,
            'lazy_days': len(lazy_days_steps)
        }

        water_stat_summary = {
            'avg': water_stat_avg, 'filled_days': sum(1 for w in water_stat if w.get('water_flag') != 'NO'),
            'norm_days': sum(1 for w in water_stat if w.get('water_flag') == 'OK'),
            'dry_days_avg': sum(water_dry_days) / len(water_dry_days) * 1000
            if len(water_dry_days) else None,
            'dry_days_count': len(water_dry_days)
        }

        hunger_stat = sorted(hunger_stat, key=lambda x: x.get('date'))
        hunger_stat_summary = {
            'stat' : [h.get('hunger') for h in hunger_stat],
            'days' : sum(1 for h in hunger_stat if h.get('hunger', 'NA') != 'NA'),
            'hunger_total' : sum(h.get('hunger') for h in hunger_stat if h.get('hunger', 'NA') != 'NA' ),
        }

        faults = MealFault.objects.filter(is_active=True).order_by('-is_public', 'code').all()

        faults_dict = {f.code: f for f in faults}

        faults_stat_qs = DiaryMealFault.objects.filter(
            diary_record__in=diaries, fault__in=faults).values(
            'diary_record__date', 'fault__code').annotate(
            total=Count('fault__code')).order_by('diary_record__date')

        faults_data = {}
        for r in faults_stat_qs:
            faults_data.setdefault(r.get('diary_record__date'), {})[r.get('fault__code')] = r.get('total', 0)

        faults_list = [f.code for f in faults]

        faults_stat = []
        balance_stat = []
        opp_stat = []

        for _faultcode in faults_list:
            _fault_stat_rec = {
                "code": _faultcode,
                # "fault": faults_dict[_faultcode],
                "fault": MealFaultsSerializer(faults_dict[_faultcode]).data,
                "stat": [faults_data.get(d, {}).get(_faultcode, 0) for d in dates_list],
            }

            _fault_stat_rec['days'] = sum(map(lambda x: x > 0, _fault_stat_rec['stat']))
            _fault_stat_rec['count'] = sum(_fault_stat_rec['stat'])

            if sum(_fault_stat_rec['stat']) > 0:
                if faults_dict[_faultcode].is_public:
                    faults_stat.append(_fault_stat_rec)
                elif faults_dict[_faultcode].is_manual:
                    balance_stat.append(_fault_stat_rec)
                else:
                    opp_stat.append(_fault_stat_rec)

        faults_stat = sorted(faults_stat, key=itemgetter('days'), reverse=True)
        balance_stat = sorted(balance_stat, key=itemgetter('days'), reverse=True)
        opp_stat = sorted(opp_stat, key=itemgetter('days'), reverse=True)

        user_stat = calculate_user_stat(int(user_id), interval_start, interval_end)

        # meal_ok_days_count = user_stat.get('pers_rec_ok_days_count')
        # meal_filled_days_count = user_stat.get('pers_rec_total_days_count')

        meal_filled_days_count = len(meal_filled_days)
        meal_ok_days_count = sum(1 for m in meal_filled_days
                                 if m.get('meals') and m.get('meals') >= 8)  # m.get('pers_req_flag') == 'OK' and

        meal_ok_days_percent = meal_ok_days_count / meal_filled_days_count * 100 if meal_filled_days_count else 0

        meal_fault_days = [m.get('meals') for m in meal_filled_days
                           if m.get('meals') and m.get('meals') < 8]  # if m.get('pers_req_flag') != 'OK' and
        if len(meal_fault_days):
            meals_avg = sum(m for m in meal_fault_days) * 10 / len(meal_fault_days)
        else:
            meals_avg = 0

        # нужны ли еще ограничения ? не может ли быть пользователь с 4х летней историей..
        # кажется не оч актуальным, если он рывками вносил записи
        first_record = DiaryRecord.objects.filter(
            user=requested_user,
            trueweight__isnull=False,
            date__lt=interval_start
        ).order_by('date').first()

        last_record = DiaryRecord.objects.filter(
            user=requested_user,
            trueweight__isnull=False,
            date__lt=interval_start
        ).order_by('-date').first()

        prev_trueweight_delta_weekly = None
        prev_delta = None

        if first_record and last_record:
            prev_delta = last_record.trueweight - first_record.trueweight
            weeks_count = (last_record.date - first_record.date).days / 7

            if weeks_count > 0:
                prev_trueweight_delta_weekly = str(round(prev_delta / Decimal(weeks_count), 2))

        weight_stat = {
            'trueweight_delta_interval': user_stat.get('trueweight_delta_interval'),
            'trueweight_delta_weekly': user_stat.get('trueweight_delta_weekly'),

            'prev_trueweight_delta_interval': prev_delta,
            'prev_trueweight_delta_weekly': prev_trueweight_delta_weekly,
        }

        meal_stat = {
            'filled_days': meal_filled_days_count,
            'ok_days': meal_ok_days_count,
            'ok_days_percent': meal_ok_days_percent,

            'fault_days': len(meal_fault_days),
            'fault_days_meals_avg': meals_avg,

            'faults_sum': user_stat.get('faults_sum'),
            'faulty_days_count': user_stat.get('faulty_days_count')
        }

        component_types_list = [
            {
                'code': 'desert',
                'title': 'Десерт',
            },
            {
                'code': 'frrr',
                'title': 'Фрукты/сухофрукты',
            },
            {
                'code': 'alco',
                'title': 'Алкоголь',
            },
            {
                'code': 'fat',
                'title': 'Жирные продукты',
            },
            {
                'code': 'fatcarb',
                'title': 'Сочетания жиров с углеводами',
            },
        ]

        component_types_codes = [c['code'] for c in component_types_list]
        comp_stat_qs = MealComponent.objects.filter(
            meal__diary__in=diaries, component_type__in=component_types_codes,
        ).values('meal__diary__date', 'component_type').annotate(
            total=Count('component_type'),
            meals_count=Count('meal_id', distinct=True),
            total_weight=Sum('weight')
        ).order_by('meal__diary__date')

        comp_stat_data = defaultdict(dict)
        for r in comp_stat_qs:
            comp_stat_data[r.get('meal__diary__date')][r.get('component_type')] = {
                'cnt': r.get('total', 0),
                'weight': r.get('total_weight', 0),
            }

        fruit_stat_qs = MealComponent.objects.filter(
            meal__diary__in=diaries, component_type__in=['fruit', 'dfruit'],
        ).values('meal__diary__date').annotate(
            meals_count=Count('meal_id', distinct=True),
            total_weight=Sum('weight')
        ).order_by('meal__diary__date')

        for r in fruit_stat_qs:
            comp_stat_data[r.get('meal__diary__date')]['frrr'] = {
                'cnt': r.get('meals_count', 0),
                'weight': r.get('total_weight', 0),
            }

        comp_stat = []

        for _comp in component_types_list:
            _item = {
                'code': _comp['code'],
                'title': _comp['title'],
                'stat': [comp_stat_data.get(d, {}).get(_comp['code'], {}).get('cnt', 0) for d in dates_list],
                'weight': sum([comp_stat_data.get(d, {}).get(_comp['code'], {}).get('weight', 0) for d in dates_list]),
            }

            _item['days'] = sum(map(lambda x: x > 0, _item['stat']))
            _item['count'] = sum(_item['stat'])

            comp_stat.append(_item)

        _item = {
            'code': 'overcalory',
            'title': "Дополнительные продукты (*)",
            'stat': [int(diaries_dict[d].is_overcalory) if d in diaries_dict else 0 for d in dates_list],
        }

        _item['days'] = sum(map(lambda x: x > 0, _item['stat']))
        _item['count'] = sum(_item['stat'])

        comp_stat.append(_item)

        snack_stat_qs = DiaryMeal.objects.filter(
            diary__in=diaries, meal_type=DiaryMeal.MEAL_TYPE_SNACK,
        ).values('diary__date').annotate(total=Count('diary__date')).order_by(
            'diary__date')

        snack_stat_data = {r['diary__date']: r['total'] for r in snack_stat_qs}

        _item = {
            'code': 'snacks',
            'title': "Перекусы",
            'stat': [snack_stat_data.get(d, 0) for d in dates_list],
        }

        _item['days'] = sum(map(lambda x: x > 0, _item['stat']))
        _item['count'] = sum(_item['stat'])

        comp_stat.append(_item)

        ufs_stat_qs = MealComponent.objects.filter(
            meal__diary__in=diaries, meal_product__component_type='unknown',
            details_carb__isnull=True,
            details_fat__isnull=True,
            details_protein__isnull=True
        ).values('meal__diary').annotate(total=Count('meal__diary'), total_weight=Sum('weight')).order_by('meal__diary')

        ufs_stat_data = {r['meal__diary']: {'cnt': r.get(
            'total', 0), 'weight': r.get('total_weight', 0)} for r in ufs_stat_qs}

        _item = {
            'code': 'unknown',
            'title': "НЁХ",
            'stat': [ufs_stat_data.get(d, {}).get('cnt', 0) for d in dates_list],
            'weight': sum([ufs_stat_data.get(d, {}).get('weight', 0) for d in dates_list]),
        }

        _item['days'] = sum(map(lambda x: x > 0, _item['stat']))
        _item['count'] = sum(_item['stat'])

        comp_stat.append(_item)

        comp_stat = [f for f in comp_stat if f['count'] > 0]

        comp_stat = sorted(comp_stat, key=itemgetter('days'), reverse=True)

        product_tags_stat = []

        product_tags_to_process = MealProductTag.objects.filter(is_analytical=True).all()

        # TODO тут не масло масленное в проверках ?
        tags_stat_qs = MealComponent.objects.filter(
            meal__diary__in=diaries, meal_product__tags__in=product_tags_to_process,
            meal_product__tags__is_analytical=True
        ).values('meal__diary__date', 'meal_product__tags__id').annotate(
            total=Count('pk'),
            total_weight=Sum('weight'),
        ).order_by('meal__diary__date')

        tags_dict = {t.id: {'title': t.title, 'code': t.system_code} for t in product_tags_to_process}
        used_tags = set()
        tags_stat_data = defaultdict(dict)
        for r in tags_stat_qs:
            used_tags.add(r.get('meal_product__tags__id'))
            tags_stat_data[r.get('meal__diary__date')][r.get('meal_product__tags__id')] = {
                'cnt': r.get('total', 0),
                'weight': r.get('total_weight', 0),
            }

        for _tag in used_tags:
            _item = {
                'code': tags_dict.get(_tag).get('code'),
                'title': tags_dict.get(_tag).get('title'),
                'stat': [tags_stat_data.get(d, {}).get(_tag, {}).get('cnt', 0) for d in dates_list],
                'weight': sum([tags_stat_data.get(d, {}).get(_tag, {}).get('weight', 0) for d in dates_list]),
            }
            _item['days'] = sum(map(lambda x: x > 0, _item['stat']))
            _item['count'] = sum(_item['stat'])

            product_tags_stat.append(_item)

        product_tags_stat = sorted(product_tags_stat, key=itemgetter('days'), reverse=True)

        fatcarb_list = MealComponent.objects.filter(
            meal__diary__date__gte=interval_start,
            meal__diary__date__lte=interval_end,
            meal__diary__user=requested_user,
            component_type='fatcarb'
        ).values('meal_product__id').annotate(
            product_title=F('meal_product__title'),
            total=Count(1)
        ).order_by('-total').distinct()

        return Response({
            'faults_stat': faults_stat,
            'balance_stat': balance_stat,
            'opp_stat': opp_stat,
            'product_tags_stat': product_tags_stat,
            'comp_stat': comp_stat,
            'fatcarb_list': fatcarb_list,
            'water_stat': water_stat,
            'water_stat_summary': water_stat_summary,
            'hunger_stat': hunger_stat_summary,
            'dates': dates_list,
            'meal_dates': meal_dates_list,
            'meal_class_days': meal_class_days,
            "last_note": UserNoteSerializer(last_user_note).data,
            "doc_notes": UserNoteSerializer(doc_notes, many=True).data,
            "steps_stat": steps_stat,
            'meal_stat': meal_stat,
            'weight_stat': weight_stat,
            'pers_req': pers_req_flags,
            'pers_req_stat': pers_req_stat,
        })
