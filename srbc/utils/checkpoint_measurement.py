# -*- coding: utf-8 -*-

import datetime
import logging
from decimal import Decimal

import pytz
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from srbc.models import Checkpoint, DiaryRecord

logger = logging.getLogger(__name__)

START_DATE = settings.CHECKPOINT_MEASUREMENT_START_DATE


def get_nearest_saturday_in_past(date):
    """ Определяет ближайшую прошлую субботу

    :param date: дата
    :type date: datetime.date
    :return: дата ближайшей субботы
    :rtype: datetime.date
    """
    days_diff = 5 - date.weekday()
    if days_diff > 0:
        days_diff -= 7
    return date + datetime.timedelta(days=days_diff)


def get_nearest_saturday_in_future(date):
    """ Определяет ближайшую будущую субботу

    :param date: дата
    :type date: datetime.date
    :return: дата ближайшей субботы
    :rtype: datetime.date
    """
    days_diff = 5 - date.weekday()
    if days_diff < 0:
        days_diff += 7
    return date + datetime.timedelta(days=days_diff)


def is_correct_schedule_date(date):
    """ Истина - если, дата является датой запланированного расписания.

    :param date:
    :type date: datetime.date
    :rtype: bool 
    """
    return (START_DATE - date).days % 14 == 0


def get_nearest_schedule_saturday(date):
    """ Контрольная точка, с которой идет работа, определяется по общему расписанию:
    каждые две недели, по субботам, начиная со START_DATE (DEV-69) 
    
    :param date: дата
    :type date: datetime.date
    :return: дата ближайшей субботы по расписанию
    :rtype: datetime.date
    """
    if date <= START_DATE + datetime.timedelta(days=3):
        return START_DATE

    past_date = get_nearest_saturday_in_past(date)
    future_date = get_nearest_saturday_in_future(date)

    if abs(past_date - date).days <= 3 and is_correct_schedule_date(past_date):
        # scheduled saturday detected in past
        return past_date
    elif is_correct_schedule_date(future_date):
        # scheduled saturday detected in future
        return future_date
    else:
        # generate scheduled saturday in future
        return future_date + datetime.timedelta(days=7)


def get_current_checkpoint_date(wave_start_date, tz):
    """ Автоматически определяет дату контрольной точки, с которой идет работа.
    
    :param wave_start_date:
    :type wave_start_date: datetime.date
    :param tz: тайм-зона
    :type tz: unicode
    :return: дата текущей контрольной точки и доступна ли она для редактирования
    :rtype: (datetime.date, bool)
    """

    # определим день согласно тайм-зоне
    tz = pytz.timezone(tz)
    today = timezone.localdate(timezone=tz)

    # Контрольная точка, с которой идет работа, определяется автоматически.
    # Первая - в первую после старта потока (Wave) субботу
    first_checkpoint_date = get_nearest_saturday_in_future(date=wave_start_date)
    # Все остальные - по общему расписанию, каждые две недели, по субботам, начиная со START_DATE
    schedule_checkpoint_date = get_nearest_schedule_saturday(date=today)

    if abs(today - first_checkpoint_date).days <= 3:
        current_checkpoint_date = first_checkpoint_date
        is_editable = True
    else:
        current_checkpoint_date = schedule_checkpoint_date
        is_editable = abs(today - current_checkpoint_date).days <= 3

    return current_checkpoint_date, is_editable


def collect_image_info(user, date):
    """ Подсчитывает image_info для srbc.models.SRBCImage на основании переданной даты.
    
    :param user: пользователь, для которого подсчитываем image_info
    :type user: django.contrib.auth.models.User
    :param date: дата, относительно которой необходимо рассчитать дельты замеров
    :type date: datetime.date
    :return: Данные image_info (рост, имт, дельта веса, дельта замеров)
    :rtype: unicode | None
    """
    # определим начальные start_checkpoint и start_diary как ближайшие к старту потока (не раньше старта потока)
    try:
        start_checkpoint = Checkpoint.objects.filter(
            user_id=user.profile.user.id, date__gte=user.profile.wave.start_date
        ).earliest('date')
    except ObjectDoesNotExist:
        start_checkpoint = None

    try:
        _start_diary = DiaryRecord.objects.filter(
            user_id=user.profile.user.id, date__gte=user.profile.wave.start_date
        ).only('weight').earliest('date')
    except ObjectDoesNotExist:
        _start_diary = None
        start_diary_weight = None
    else:
        start_diary_weight = _start_diary.weight

    # Так как у photoset может быть еще не задан чекпоинт (photoset.checkpoint is None),
    # то определим начальные last_checkpoint и last_diary как ближайшие к ФотоЧекпоинту
    # (не старше даты загрузки контрольных фотографий)
    if start_checkpoint:
        try:
            last_checkpoint = Checkpoint.objects.filter(
                user_id=user.profile.user.id, is_measurements_done=True, date__lte=date
            ).latest('date')
        except ObjectDoesNotExist:
            last_checkpoint = None
    else:
        last_checkpoint = None

    if _start_diary:
        try:
            _last_diary = DiaryRecord.objects.filter(
                user_id=user.profile.user.id, weight__isnull=False, date__lte=date
            ).only('weight').latest('date')
        except ObjectDoesNotExist:
            last_diary_weight = None
        else:
            last_diary_weight = _last_diary.weight
    else:
        last_diary_weight = None

    # посчитаем дельты
    if start_checkpoint and last_checkpoint:
        try:
            delta_measurements = (start_checkpoint.measurements_sum - last_checkpoint.measurements_sum) / 10
        except TypeError:
            delta_measurements_info = '&Delta; суммы замеров от старта: ?'
        else:
            # '&Delta; суммы замеров от старта: %.1f см'
            # используем неразрывный пробел для того, чтобы в popover не было переноса строки
            delta_measurements_info = '&Delta;&nbsp;суммы&nbsp;замеров&nbsp;от&nbsp;старта:&nbsp;%.1f&nbsp;см' % delta_measurements

        height = last_checkpoint.measurement_height / 10
    else:
        delta_measurements_info = '&Delta; суммы замеров от старта: нет замеров'
        height = None

    if start_diary_weight and last_diary_weight:
        try:
            delta_weight = last_diary_weight - start_diary_weight
        except TypeError:
            delta_weight_info = '&Delta; веса от старта: ?'
        else:
            delta_weight_info = '&Delta; веса от старта: %.1f кг' % delta_weight

        weight = last_diary_weight
    else:
        delta_weight_info = '&Delta; веса от старта: нет замеров'
        weight = None

    height_info = 'Рост: %d' % height if height else 'Рост: нет замеров'

    if height and weight:
        imt = Decimal(10000) * weight / (Decimal(height) * Decimal(height))
        imt_info = 'ИМТ: %.2f' % imt
    else:
        imt_info = 'ИМТ: нет замеров'

    return '\n'.join([height_info, imt_info, delta_weight_info, delta_measurements_info])
