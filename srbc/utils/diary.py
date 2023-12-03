# -*- coding: utf-8 -*-
import datetime
import math
from decimal import Decimal

from crm.models import TariffHistory
from srbc.models import (
    DiaryRecord, MealComponent, Profile, MealProductModeration,
    CheckpointPhotos, SRBCImage, Checkpoint, TariffGroup)
from srbc.utils.meal_parsing import get_meal_faults
from srbc.utils.diary_meal_type import update_meal_types
from srbc.serializers.general import CheckpointPhotoSerializer, SRBCImageSerializer


def process_meal_component_by_product(meal_component, meal_product=None):
    if not meal_product:
        if meal_component.meal_product:
            meal_product = meal_component.meal_product

    if meal_component.details_protein is None or meal_component.details_carb is None or meal_component.details_fat is None:
        if meal_product:
            use_protein = meal_product.protein_percent
            use_carb = meal_product.carb_percent
            use_fat = meal_product.fat_percent
            use_is_sugar = meal_product.is_fast_carbs
            meal_component.description = "%s (БЖУ неизвестны)" % meal_product.title
        else:
            meal_component.description = "%s (БЖУ неизвестны)" % meal_component.other_title
            return meal_component
    else:
        use_protein = meal_component.details_protein
        use_carb = meal_component.details_carb
        use_fat = meal_component.details_fat
        use_is_sugar = meal_component.details_sugars
        meal_component.description = "%s (%.1f/%.1f/%.1f%s)" % (
            meal_product.title,
            meal_component.details_protein,
            meal_component.details_fat,
            meal_component.details_carb,
            ", сахара" if meal_component.details_sugars else ""
        )

    if use_is_sugar:
        meal_component.component_type = 'desert'
    elif use_protein >= use_fat and use_protein >= use_carb and use_protein >= 12:
        meal_component.component_type = 'protein'
    elif use_fat >= 10 and use_carb >= 10:
        meal_component.component_type = 'fatcarb'
    elif use_fat >= use_carb and use_fat >= 10:
        meal_component.component_type = 'fat'
    elif use_carb > 30:
        meal_component.component_type = 'rawcarb'
    elif use_carb >= 10:
        meal_component.component_type = 'carb'

    return meal_component


def diary_meal_pre_analyse(diary_record):
    # TODO: set correct product type for all products
    meal_components = MealComponent.objects.filter(meal__diary=diary_record, component_type='unknown') \
        .select_related('meal_product') \
        .all()

    for mc in meal_components:
        if not mc.meal_product:
            continue

        if mc.details_protein is None or mc.details_carb is None or mc.details_fat is None:
            use_protein = mc.meal_product.protein_percent
            use_carb = mc.meal_product.carb_percent
            use_fat = mc.meal_product.fat_percent
            use_is_sugar = mc.meal_product.is_fast_carbs
        else:
            use_protein = mc.details_protein
            use_carb = mc.details_carb
            use_fat = mc.details_fat
            use_is_sugar = mc.details_sugars

        if use_is_sugar:
            mc.component_type = 'desert'
        elif use_protein >= use_fat and use_protein >= use_carb and use_protein >= 12:
            mc.component_type = 'protein'
        elif use_fat >= 10 and use_carb >= 10:
            mc.component_type = 'fatcarb'
        elif use_fat >= use_carb and use_fat >= 10:
            mc.component_type = 'fat'
        elif use_carb > 30:
            mc.component_type = 'rawcarb'
        elif use_carb >= 10:
            mc.component_type = 'carb'

        mc.save()

    new_components = MealComponent.objects.filter(meal__diary=diary_record, component_type='new').all()
    for mc in new_components:
        ticket = MealProductModeration(meal_component_id=mc.pk, title=mc.other_title, title_source=mc.other_title)
        ticket.save()

    update_meal_types(diary_record)

    return diary_record


def diary_meal_analyse(diary_record):
    """
    :param diary_record: Объект записи дневника
    :type diary_record: srbc.models.DiaryRecord
    :return:
    """
    if diary_record.anlz_mode == DiaryRecord.ANLZ_MODE_AUTO:
        faults_list, error = get_meal_faults(diary_record)

        if error:
            diary_record.is_fake_meals = True
            diary_record.meal_status = 'FAKE'
            diary_record.is_meal_reviewed = True
            diary_record.save(update_fields=['meal_status', 'is_meal_reviewed', 'is_fake_meals'])
        else:
            faults_count = 0
            for _f in faults_list:
                _f.save()
                if _f.fault.is_public:
                    faults_count += 1

            diary_record.faults = faults_count
            diary_record.meal_status = 'DONE'
            diary_record.is_meal_reviewed = True
            diary_record.save(update_fields=['faults', 'meal_status', 'is_meal_reviewed'])

    # Проверить все продукты с неизвестным составом

    pass


def get_diary_statistics(
        user_id, start_date=None, end_date=None, as_timestamp=True, is_staff=False, add_empty_days=False):
    """ Получение данных статистики рациона в определенных временых рамках.

    В текущей реализации используется для вывода графика на фронте.

    :param user_id: идентификатор пользователя
    :type user_id: int
    :param start_date: дата, относительно которой необходимо собрать статистику
    :type start_date: datetime.date
    :param end_date: дата, относительно которой необходимо собрать статистику
    :type end_date: datetime.date
    :param as_timestamp: даты в результате будут представлены в виде timestamp
    :type as_timestamp: bool
    :param add_empty_days: если задан, то добавляет пустые точки в масиивы 'trueweight' и 'weight',
        если нет записей в БД (шаг = день)
    :type as_timestamp: bool
    :return: статистика рациона
    :rtype: dict
    """
    assert isinstance(user_id, int)
    assert isinstance(start_date, datetime.date) or (start_date is None)
    assert isinstance(end_date, datetime.date) or (end_date is None)

    diaries_qs = DiaryRecord.objects.filter(user_id=user_id)
    if start_date:
        diaries_qs = diaries_qs.filter(date__gte=start_date)
    if end_date:
        diaries_qs = diaries_qs.filter(date__lte=end_date)

    diaries_qs = diaries_qs.only(
        'date', 'weight', 'trueweight', 'steps', 'sleep', 'is_ooc', 'meals', 'faults',
        'meal_status'
    )

    initial_diary = DiaryRecord.objects.filter(user_id=user_id, weight__isnull=False) \
        .order_by('date').only('date', 'weight').first()

    data = {
        "weight": [],
        "trueweight": [],
        "steps": [],
        "sleep": [],
        "meals": [],
        "faults": [],
        "meal_reviewed": [],
        # "weight_support": [],
        # "weight_resist": [],
    }

    unix_epoch = datetime.datetime.utcfromtimestamp(0)

    _min_weight = 999
    _max_weight = 0
    _start_weight = 0
    _start_date = 0
    _end_date = None

    if initial_diary:
        if as_timestamp:
            diary_date = datetime.datetime.combine(initial_diary.date, datetime.datetime.min.time()) - unix_epoch
            diary_date = diary_date.total_seconds() * 1000.0
        else:
            diary_date = initial_diary.date

        _start_date = diary_date
        _start_weight = initial_diary.weight

    # moving_weight = []
    # moving_weight_max = []
    # moving_weight_min = []

    step_time = 24 * 60 * 60 * 1000
    prev_date = None

    for diary in diaries_qs.order_by('date').iterator():
        if as_timestamp:
            diary_date = datetime.datetime.combine(diary.date, datetime.datetime.min.time()) - unix_epoch
            diary_date = diary_date.total_seconds() * 1000.0
        else:
            diary_date = diary.date

        if add_empty_days:
            # проверяем нет ли разрыва
            if prev_date and diary_date - prev_date > step_time:
                daysCount = (int)((diary_date - prev_date) / step_time)

                # Добавляем пустые записи
                for i in range(1, daysCount):
                    empty_date = prev_date + i * step_time
                    data['weight'].append([empty_date, None])
                    data['trueweight'].append([empty_date, None])

            prev_date = diary_date

        data['weight'].append([diary_date, diary.weight])

        if diary.weight and diary.weight < _min_weight:
            _min_weight = diary.weight

        if diary.weight and diary.weight > _max_weight:
            _max_weight = diary.weight

        if (not _end_date) or (_end_date is None) or (diary_date > _end_date):
            _end_date = diary_date

        # if diary.weight is not None:
        #     moving_weight.insert(0, diary.weight)

        # moving_weight = moving_weight[:21]

        # if len(moving_weight):
        #     moving_weight_max.insert(0, max(moving_weight))
        #     moving_weight_max = moving_weight_max[:7]
        #
        #     moving_weight_min.insert(0, min(moving_weight))
        #     moving_weight_min = moving_weight_min[:7]

        #     data['weight_support'].append([diary_date, sum(moving_weight_min) / len(moving_weight_min)])
        #     data['weight_resist'].append([diary_date, sum(moving_weight_max) / len(moving_weight_max)])
        # else:
        #     data['weight_support'].append([diary_date, None])
        #     data['weight_resist'].append([diary_date, None])

        if diary.trueweight is not None:
            data['trueweight'].append([diary_date, diary.trueweight])
        elif add_empty_days:
            data['trueweight'].append([diary_date, None])

        if diary.steps is not None:
            data['steps'].append([diary_date, Decimal(diary.steps) / 10000 * 100])
        else:
            data['steps'].append([diary_date, None])
        if diary.sleep is not None:
            data['sleep'].append([diary_date, Decimal(min(diary.sleep, 8.)) / 8 * 100])
        else:
            data['sleep'].append([diary_date, None])

        if diary.is_ooc:
            data['meals'].append([diary_date, 0])
            data['faults'].append([diary_date, 3])
        else:
            data['meals'].append([diary_date, diary.meals])

            if diary.faults:
                data['faults'].append([diary_date, diary.faults])
            else:
                data['faults'].append([diary_date, None])

        data['meal_reviewed'].append([diary_date, diary.meal_status == 'DONE'])

    profile = Profile.objects.get(user_id=user_id)
    goal_weight = None

    if profile.goal_weight and (profile.display_goal_weight or is_staff):
        _min_weight = min(_min_weight, profile.goal_weight)
        _max_weight = max(_min_weight, profile.goal_weight)
        goal_weight = profile.goal_weight

    data.update({
        'min_weight': math.floor(_min_weight) - 1,
        'max_weight': math.ceil(_max_weight) + 1,
        'start_weight': _start_weight,
        'goal_weight': goal_weight,
        'start_date': _start_date,
        'end_date': _end_date
    })

    return data


def calculate_user_stat(user_id, start_date, end_date, as_timestamp=True):
    """ Подсчитывает статистику пользователя.

    :param user_id: идентификатор пользователя
    :type user_id: int
    :param start_date: дата, относительно которой необходимо собрать статистику
    :type start_date: datetime.date
    :param end_date: дата, относительно которой необходимо собрать статистику
    :type end_date: datetime.date
    :param as_timestamp: даты в результате будут представлены в виде timestamp
    :type as_timestamp: bool
    :return: статистика рациона
    :rtype: dict
    """
    assert isinstance(user_id, int)
    assert isinstance(start_date, datetime.date) or (start_date is None)
    assert isinstance(end_date, datetime.date) or (end_date is None)

    weight_init = 0
    trueweight_init = 0
    weight_last = None
    weight_date_last = None
    trueweight_last = None
    faults_sum = 0
    faulty_days_count = 0
    meal_days_total = 0
    steps_sum = 0
    steps_achieved_days_count = 0
    steps_days_total = 0
    sleep_sum = 0
    sleep_achieved_days_count = 0
    sleep_days_total = 0

    data = get_diary_statistics(user_id=user_id, start_date=start_date, end_date=end_date, as_timestamp=as_timestamp)

    user_meals = DiaryRecord.objects.filter(meal_status='DONE', user_id=user_id)

    if start_date:
        user_meals = user_meals.filter(date__gte=start_date)
    if end_date:
        user_meals = user_meals.filter(date__lte=end_date)

    pers_rec_total_days = user_meals.filter(pers_rec_flag__in=['F', 'OK']).count()
    pers_rec_ok_days = user_meals.filter(pers_rec_flag__in=['OK']).count()

    for item in data['weight']:
        w = item[1]
        if w is None:
            continue

        if not weight_init:
            weight_init = w

        weight_last = w

    for item in data['trueweight']:
        tw = item[1]
        if tw is None:
            continue

        if not trueweight_init:
            trueweight_init = tw

        trueweight_last = tw
        weight_date_last = item[0]

    for i, item in enumerate(data['meals']):
        m = data['meal_reviewed'][i][1]
        f = data['faults'][i][1]
        meal_days_total += 1 if m else 0
        if m is None and not f:
            continue

        if f:
            faults_sum += f
            faulty_days_count += 1

    for item in data['steps']:
        s = item[1]
        if s is None:
            continue

        steps_days_total += 1
        steps_sum += s

        if s >= 100:
            steps_achieved_days_count += 1

    for item in data['sleep']:
        s = item[1]
        if s is None:
            continue

        sleep_days_total += 1
        sleep_sum += s

        if s >= 100:
            sleep_achieved_days_count += 1

    weeks_count = (weight_date_last - data['start_date']) / (86400 * 1000 * 7) if weight_date_last else None
    if weeks_count:
        trueweight_delta_weekly = str(round((trueweight_last - data['start_weight']) / Decimal(weeks_count), 2))
    else:
        trueweight_delta_weekly = None

    return {
        "weight_init": weight_init,
        "trueweight_init": trueweight_init,
        "weight_last": weight_last,
        "weight_date_last": weight_date_last,
        "trueweight_last": trueweight_last,
        "faults_sum": faults_sum,
        "faulty_days_count": faulty_days_count,
        "pers_rec_ok_days_count": pers_rec_ok_days,
        "pers_rec_total_days_count": pers_rec_total_days,
        "meal_days_total": meal_days_total,
        "steps_sum": steps_sum,
        "steps_achieved_days_count": steps_achieved_days_count,
        "steps_days_total": steps_days_total,
        "sleep_sum": sleep_sum,
        "sleep_achieved_days_count": sleep_achieved_days_count,
        "sleep_days_total": sleep_days_total,
        "weight_delta_start": round((weight_last - data['start_weight']), 1) if weight_last else None,
        "trueweight_delta_start": round((trueweight_last - data['start_weight']), 1) if trueweight_last else None,
        "trueweight_percent_start": round((data['start_weight'] - trueweight_last) * 100 / data['start_weight'],
                                          1) if trueweight_last else None,
        "weeks_count": math.floor(weeks_count) if weeks_count else None,
        "trueweight_delta_weekly": trueweight_delta_weekly,
        "weight_delta_interval": round(weight_last - weight_init, 1) if weight_last else None,
        "trueweight_delta_interval": round(trueweight_last - trueweight_init, 1) if trueweight_last else None,
        "steps_avg_interval": "%.2f%%" % (steps_sum / steps_days_total) if steps_days_total else None,
        "sleep_avg_interval": "%.0f%%" % (sleep_sum / sleep_days_total) if sleep_days_total else None,
    }


def get_checkpoint_photo_set(user_id):
    photos = CheckpointPhotos.objects.filter(user_id=user_id, status__in=('APPROVED', 'NEW')).order_by('-date')

    photo_collages = SRBCImage.objects.filter(
        user_id=user_id,
        image_type__in=[
            'CHECKPOINT_PHOTO',
            'CHECKPOINT_PHOTO_FRONT',
            'CHECKPOINT_PHOTO_SIDE',
            'CHECKPOINT_PHOTO_REAR',
        ]
    ).all()

    collages_by_date = {}
    for collage in photo_collages:
        if collage.date not in collages_by_date:
            collages_by_date[collage.date] = []

        collages_by_date[collage.date].append(SRBCImageSerializer(instance=collage).data)

    # наличие замеров для текущего потока
    wave_checkpoints_exists = Checkpoint.objects.filter(
        user_id=user_id, date__gte=Profile.objects.get(user_id=user_id).wave.start_date
    ).exists()

    photo_data = []
    for i in photos:
        instance = CheckpointPhotoSerializer(instance=i).data
        instance['collages'] = collages_by_date.get(i.date)
        instance['wave_checkpoints_exists'] = wave_checkpoints_exists
        photo_data.append(instance)

    return photo_data


def get_anlz_mode(user, date):
    mode = None
    no_access_array = [TariffGroup.DIARY_ACCESS_READ, TariffGroup.DIARY_ACCESS_WRITE]

    # возвращает типо оцифровки для заданного пользователя на заданную дату
    active_th = user.profile.active_tariff_history

    if active_th and active_th.valid_from <= date <= active_th.valid_until:
        if active_th.tariff.tariff_group.diary_access in no_access_array:
            mode = DiaryRecord.ANLZ_MODE_NO

        elif active_th.tariff.tariff_group.diary_access == TariffGroup.DIARY_ACCESS_ANLZ_AUTO:
            mode = DiaryRecord.ANLZ_MODE_AUTO

        else:
            mode = DiaryRecord.ANLZ_MODE_MANUAL
    else:
        # дата не относится к активной ТХ, находим запись и смотрим уровень доступа там
        diary_th = TariffHistory.objects.filter(
            user_id=user.pk,
            valid_until__gte=date,
            valid_from__lte=date,
            is_active=True,
        ).first()

        # если записи нет, то просто вренем отсутствие доступа
        if not diary_th:
            mode = DiaryRecord.ANLZ_MODE_NO
        else:
            # если нашли запись, то сравниваем доступ к анализу дневника и выбираем минимальный
            if (active_th and active_th.tariff.tariff_group.diary_access in no_access_array) or \
                    diary_th.tariff.tariff_group.diary_access in no_access_array:
                mode = DiaryRecord.ANLZ_MODE_NO

            elif (active_th and active_th.tariff.tariff_group.diary_access == TariffGroup.DIARY_ACCESS_ANLZ_AUTO) or \
                    diary_th.tariff.tariff_group.diary_access == TariffGroup.DIARY_ACCESS_ANLZ_AUTO:
                mode = DiaryRecord.ANLZ_MODE_AUTO

            else:
                mode = DiaryRecord.ANLZ_MODE_MANUAL

     # если в профайле установлен режим автооцифровки , то "понижаем"
    if active_th and active_th.tariff.tariff_group.is_wave and \
        mode == DiaryRecord.ANLZ_MODE_MANUAL and \
            user.profile.meal_analyze_mode == Profile.MEAL_ANALYZE_MODE_AUTO:
        mode = DiaryRecord.ANLZ_MODE_AUTO

    return mode
