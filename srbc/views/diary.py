# -*- coding: utf-8 -*-
import hashlib
import io
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from time import time

import pytz
from PIL import Image, ExifTags, ImageFile
from django.db import transaction
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import redirect, render
from django.utils import dateformat
from django.utils import timezone
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from srbc.decorators import validate_user, has_desktop_access
from srbc.forms import DiaryDataForm
from srbc.models import DiaryRecord, CheckpointPhotos, Profile, TariffGroup
from srbc.serializers.general import ProfileSerializer
from srbc.tasks import update_collages_image_info, create_or_update_data_image, update_diary_trueweight
from srbc.utils.meal_recommenation import get_meal_recommendations
from srbc.utils.srbc_image import save_image, put_image_in_memory
from srbc.views.collage import generate_data_image
from srbc.xiaomi import XiaomiManager

logger = logging.getLogger(__name__)
ImageFile.LOAD_TRUNCATED_IMAGES = True


@login_required
@has_desktop_access
@validate_user
def user_day_meals_form(request, data_date=None):
    if not data_date:
        today_str = timezone.localtime().strftime("%Y-%m-%d")
        return redirect('/diary/%s/meals/' % today_str)

    tz = pytz.timezone(request.user.profile.timezone)
    input_date = datetime.strptime(data_date, "%Y-%m-%d")
    today = tz.localize(input_date)
    # Can not edit future values and/or too old values.

    yesterday = tz.localize(input_date - timedelta(days=1))
    tomorrow = tz.localize(input_date + timedelta(days=1))

    if tomorrow.date() > timezone.localtime().date() + timedelta(days=1):
        tomorrow = None

    diary = DiaryRecord.objects.filter(date=today.date(), user=request.user).first()

    if request.user.profile.tariff and request.user.profile.tariff.tariff_group.diary_access == TariffGroup.DIARY_ACCESS_READ:
        template = 'srbc/diary_form_meals_reviewed.html'
    elif (diary is not None) and diary.is_meal_validated:
        template = 'srbc/diary_form_meals_reviewed.html'
    else:
        template = 'srbc/diary_form_meals.html'

    profile_serialized = ProfileSerializer(request.user.profile)
    meal_recommendations = get_meal_recommendations(user_id=request.user.id)

    return render(
        request,
        template,
        {
            'today': today.date(),
            'yesterday': yesterday.date(),
            'tomorrow': tomorrow.date() if tomorrow else None,
            "profile_user": request.user.profile,
            "profile_serialized": profile_serialized.data,
            "meal_recommendations": meal_recommendations,
        }
    )


@login_required
@has_desktop_access
@validate_user
def checkpoint_measurements_app(request):
    return render(
        request,
        'srbc/checkpoint_form_measurements.html',
        {
            "may_be_reviewed": request.user.profile.tariff.tariff_group.expertise_access
        }
    )


@login_required
@has_desktop_access
@validate_user
def checkpoint_photos_app(request):
    return render(
        request,
        'srbc/checkpoint_form_collages.html',
        {
        }
    )


@login_required
@has_desktop_access
@validate_user
# @transaction.atomic
def user_day_data_form(request, data_date=None):
    """ Обрабатывает и сохраняет данные (форму) дневника.

    :param request:
    :type request: django.core.handlers.wsgi.WSGIRequest
    :param data_date: день дневника
    :type data_date: str
    """

    def get_diary_initial(diary_today):
        sleep = Decimal(int((diary_today.sleep or 0) * 4)) / 4

        diary_today.sleep_hours = int(sleep)
        diary_today.sleep_minutes = int((sleep - diary_today.sleep_hours) * 60)

        diary_initial = {
            'sleep_hours': diary_today.sleep_hours,
            'sleep_minutes': diary_today.sleep_minutes,
            'steps': diary_today.steps,
            'weight': diary_today.weight,
            'meals_score': diary_today.meals,
            'meals_faults': diary_today.faults,
            'meals_overcalory': diary_today.is_overcalory,
        }

        return diary_initial

    if not data_date:
        today_str = timezone.localtime().strftime("%Y-%m-%d")
        return redirect('/diary/%s/data/' % today_str)

    tz = pytz.timezone(request.user.profile.timezone)
    input_date = datetime.strptime(data_date, "%Y-%m-%d")
    today = tz.localize(input_date)
    # Can not edit future values and/or too old values.
    readonly = False

    if timezone.localtime() - timedelta(days=7) > today:
        readonly = True

    if timezone.localtime() + timedelta(days=1) < today:
        readonly = True

    # timedelta применяем к "чистой" дате, без часовых поясов,
    # иначе может сбиться при DST + переход на летнее/зимнее время
    yesterday = tz.localize(input_date - timedelta(days=1))
    tomorrow = tz.localize(input_date + timedelta(days=1))

    if tomorrow.date() > timezone.localtime().date():
        tomorrow = None

    is_dirty = False
    is_weight_dirty = False

    # вынесем вперед, общий момент
    try:
        _diary_prev = DiaryRecord.objects. \
            filter(user=request.user, date__lt=today.date(), weight__isnull=False).only('weight').latest('date')
    except ObjectDoesNotExist:
        # предыдущей записи дневника нет
        diary_prev_weight = None
    else:
        diary_prev_weight = _diary_prev.weight

    if request.method == 'POST' and not readonly:

        with transaction.atomic():
            # Locking
            Profile.objects.select_for_update().get(user=request.user)

            diary_today = DiaryRecord.objects.filter(user=request.user, date=today.date()).first()
            if not diary_today:
                diary_today = DiaryRecord(user=request.user, date=today.date())
                # diary_today.save()

            diary_initial = get_diary_initial(diary_today)

            post = request.POST.copy()
            if 'weight' in post:
                post['weight'] = post['weight'].replace(',', '.')

            if 'steps' in post:
                post['steps'] = post['steps'].replace(',', '')
                post['steps'] = post['steps'].replace(' ', '')

            form = DiaryDataForm(post, initial=diary_initial)
            if form.is_valid():

                s_hours = form.cleaned_data.get('sleep_hours') or 0
                s_minutes = form.cleaned_data.get('sleep_minutes') or 0
                sleep_value = Decimal(s_hours * 60 + s_minutes) / 60

                now = timezone.now()

                if diary_today.weight != form.cleaned_data.get('weight'):
                    is_weight_dirty = True
                    is_dirty = True
                    diary_today.weight = form.cleaned_data.get('weight')
                    diary_today.last_weight_updated = now

                if diary_today.steps != form.cleaned_data.get('steps'):
                    is_dirty = True
                    diary_today.steps = form.cleaned_data.get('steps')
                    diary_today.last_steps_updated = now

                if diary_today.sleep != sleep_value:
                    is_dirty = True
                    diary_today.sleep = sleep_value
                    diary_today.last_sleep_updated = now

                if is_dirty:
                    diary_today.last_data_updated = now

                    if is_weight_dirty:
                        # если скинули вес, то дополнительно обнуллим trueweight
                        if not diary_today.weight:
                            diary_today.trueweight = None

                    diary_today.save()

    else:
        # немного дублируем код, чтобы в гете не ставить блокировку
        diary_today = DiaryRecord.objects.filter(user=request.user, date=today.date()).first()
        if not diary_today:
            diary_today = DiaryRecord(user=request.user, date=today.date())

        diary_initial = get_diary_initial(diary_today)

        form = DiaryDataForm(initial=diary_initial)

    if is_dirty:
        if is_weight_dirty:
            update_diary_trueweight.delay(user_id=request.user.id, start_from=diary_today.date)
            update_collages_image_info.delay(diary_record_id=diary_today.pk)

        create_or_update_data_image.delay(user_id=request.user.pk, diary_record_id=diary_today.pk)

    return render(
        request,
        'srbc/diary_form_data.html',
        {
            'readonly': readonly,
            'form': form,
            'today': today.date(),
            'yesterday': yesterday.date(),
            'tomorrow': tomorrow.date() if tomorrow else None,
            'diary': diary_today,
            'diary_prev_weight': diary_prev_weight,
            'hours_range': list(range(0, 24)),
            'minutes_range': list(range(0, 60, 15)),
        }
    )


@login_required
@has_desktop_access
@validate_user
def user_photo_upload(request):
    action = 'form'

    def raise_error(error):
        return render(
            request,
            'srbc/user_photo_upload.html',
            {
                "error": error,
                "action": action,
            }
        )

    checkpoint_date = None

    min_width = 800
    min_height = 1200

    hashes = []

    if request.method == 'POST':
        types = ['face', 'side', 'rear']

        photos = {}

        for name in types:
            file_obj = request.FILES.get(name)
            if not file_obj:
                return raise_error("Необходимо загрузить три фотографии")

            try:
                img_obj = Image.open(file_obj)
            except IOError:
                return raise_error("Недопустимый формат одного или более файлов")

            try:
                photo_exif = img_obj._getexif()
            except AttributeError:
                # не у всех типов изображений можно загрузить EXIF таким образом (например, у PNG)
                return raise_error("Попробуйте загрузить фотографии в JPG формате")

            if not photo_exif:
                return raise_error("Необходимо загрузить неотредактированные исходники фотографий")

            tags_to_parse = [
                'DateTime', 'DateTimeOriginal', 'Orientation',
            ]

            exif_tags = {ExifTags.TAGS[k]: v for k, v in photo_exif.items() if
                         k in ExifTags.TAGS and ExifTags.TAGS[k] in tags_to_parse}

            photo_date = exif_tags.get('DateTime') or exif_tags.get('DateTimeOriginal')

            if photo_date is None:
                return raise_error("Необходимо загрузить неотредактированные исходники фотографий")
            else:
                photo_date = photo_date[:10]

            if not checkpoint_date:
                checkpoint_date = photo_date
            else:
                if checkpoint_date != photo_date:
                    return raise_error("Все три фотографии должны быть сделаны в один день")

            orientation = exif_tags.get('Orientation')

            if orientation:
                if orientation == 3:
                    img_obj = img_obj.rotate(180, expand=True)
                elif orientation == 6:
                    img_obj = img_obj.rotate(270, expand=True)
                elif orientation == 8:
                    img_obj = img_obj.rotate(90, expand=True)

            width, height = img_obj.size

            if width < min_width or height < min_height:
                return raise_error("Размер каждой фотографии (ШхВ) должен быть не менее чем 800x1200")

            hashes.append(
                hashlib.md5(img_obj.tobytes()).hexdigest()
            )

            file_io = io.BytesIO()
            img_obj.save(file_io, format='JPEG', quality=95)

            img_file = InMemoryUploadedFile(
                file_io, None, '%s.jpg' % name, 'image/jpeg',
                file_io.getbuffer().nbytes, None
            )

            photos[name] = img_file

        tz = pytz.timezone(request.user.profile.timezone)
        checkpoint_date = checkpoint_date.replace('-', ':')
        checkpoint_date = tz.localize(datetime.strptime(checkpoint_date, "%Y:%m:%d")).date()

        checkpoint = CheckpointPhotos.objects.filter(user=request.user, date=checkpoint_date).first()
        if checkpoint:
            if checkpoint.status == 'APPROVED':
                return raise_error("Фотографии за эту дату уже загружены и проверены")
        else:
            checkpoint = CheckpointPhotos(user=request.user, date=checkpoint_date)

        if len(list(set(hashes))) != 3:
            return raise_error("Нужны три РАЗНЫХ фотографии – с трёх ракурсов")

        checkpoints_exists = CheckpointPhotos.objects.filter(status='APPROVED', user=request.user).exists()

        checkpoint.front_image = photos.get('face')
        checkpoint.side_image = photos.get('side')
        checkpoint.rear_image = photos.get('rear')
        checkpoint.status = 'APPROVED' if checkpoints_exists else 'NEW'

        checkpoint.save()
        action = 'success'

    return render(
        request,
        'srbc/user_photo_upload.html',
        {
            "action": action,
            "checkpoint_date": checkpoint_date,
        }
    )


@swagger_auto_schema(
    method='get',
    **swagger_docs['GET /v1/tracker/mifit/load/']
)
@api_view(('GET',))
@renderer_classes((JSONRenderer,))
@login_required
@has_desktop_access
@validate_user
def load_tracker_data_mifit(request, diary_date=None):
    return Response({})
