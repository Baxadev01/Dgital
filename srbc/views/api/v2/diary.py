# -*- coding: utf-8 -*-
import base64
import datetime
import logging
import re
from uuid import uuid4

import pytz
import wikipedia
from PIL import Image

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db.models import DateField, Prefetch
from django.http.response import Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.utils import timezone, dateformat
from django_telegrambot.apps import DjangoTelegramBot
from pymorphy2 import MorphAnalyzer
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_tracking.mixins import LoggingMixin

from content.utils import store_dialogue_reply
from srbc.models import (
    DiaryRecord, User, SRBCImage, DiaryMeal, MealComponent, Checkpoint, Profile, MealFault,
    ParticipationGoal, CheckpointPhotos, MealProduct, DiaryMealFault,
)
from srbc.permissions import UserCanUseDiary
from srbc.serializers.general import (
    CheckpointPhotoSerializer, SRBCImageSerializer, ParticipationGoalSerializer,
    ParticipationGoalOrderSerializer, DiaryRecordSerializer, DiaryMealDataSerializer,
    DiaryReviewSerializer,
    MealFaultsSerializer, DiaryMealDataAdminSerializer,
    ParticipantDiaryReviewSerializer,
    MealFaultsAdminSerializer,
    MealProductSerializer,  DiaryTodaySerializer,
    DiaryTomorrowSerializer, ParticipationGoalStatusSerializer,
)

from srbc.utils.checkpoint_measurement import collect_image_info
from srbc.utils.diary import get_diary_statistics, diary_meal_analyse, diary_meal_pre_analyse, get_anlz_mode
from srbc.utils.permissions import HasStaffPermission, IsActiveUser, check_user_id, IsWaveUser, \
    HasDiaryReadAccess, HasDiaryWriteAccess
from srbc.utils.srbc_image import (
    build_3view_collage, build_compare_collages, create_meal_collage, put_image_in_memory,
    draw_fake_mark, clean_exif_data,
)
from srbc.utils.meal_recommenation import get_meal_recommendations

from drf_yasg.utils import swagger_auto_schema
from swagger_docs import swagger_docs


logger = logging.getLogger('DIARY_API')


class DiaryMealSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser, IsWaveUser,)
    sensitive_fields = {'image'}

    def get_permissions(self):
        if self.action in ['meals_get']:
            return [IsAuthenticated(), HasDiaryReadAccess()]
        else:
            return [IsAuthenticated(), HasDiaryWriteAccess()]

    @staticmethod
    def detect_meal_readonly(user, diary_date):
        readonly = False
        tz = pytz.timezone(user.profile.timezone)
        today = tz.localize(datetime.datetime.strptime(diary_date, "%Y-%m-%d")).date()
        # Can not edit future values and/or too old values.
        if (timezone.localtime() - datetime.timedelta(days=user.profile.meal_days_allowed_delay)).date() > today:
            readonly = True

        # вычисляем именно от таймзоны юзера, иначе пользователи
        # с большой "+" зоной не могут редактировать
        if (datetime.datetime.now(tz) + datetime.timedelta(days=1)).date() < today:
            readonly = True

        return readonly

    @staticmethod
    # @transaction.atomic
    def meals_get(request, diary_date, diary_user=None):
        if not diary_user or not request.user.is_staff:
            diary_user = request.user.pk
            admin_mode = False
        else:
            admin_mode = True

        diary_user = User.objects.select_related('profile').get(pk=diary_user)

        # Locking
        # Profile.objects.select_for_update().get(user=diary_user)

        try:
            diary = DiaryRecord.objects.get(user=diary_user, date=diary_date)
        except ObjectDoesNotExist:
            diary = DiaryRecord(user=diary_user, date=diary_date)

        readonly = DiaryMealSet.detect_meal_readonly(user=request.user, diary_date=diary_date)

        if not diary.anlz_mode or (
                diary.meal_status == DiaryRecord.MEAL_STATUS_NOT_READY and not readonly):
            diary.anlz_mode = get_anlz_mode(diary_user, datetime.datetime.strptime(diary_date, '%Y-%m-%d').date())

        if readonly and not admin_mode:
            diary.is_meal_validated = True
            diary.is_fake_meals = True

        if not request.user.is_staff:
            faults_to_show = [f for f in diary.faults_list.filter(fault__is_public=True).all()]
            # logging.info("=" * 60)
            # logging.info(faults_to_show)
            diary.faults_list.set(faults_to_show)
            serialized = DiaryMealDataSerializer(instance=diary)
        else:
            serialized = DiaryMealDataAdminSerializer(instance=diary)
        return Response(serialized.data)

    @staticmethod
    def save_diary_meal_image(user, image_data):
        """ Проверят и сохраняет изображение в памяти.

        :param user:
        :type user: django.contrib.auth.models.User
        :param image_data: base64 image data
        :type image_data: str
        :return: image and exif
        :rtype: (django.core.files.uploadedfile.InMemoryUploadedFile, dict) | (None, dict)
        """
        img_format, img_str = image_data.split(';base64,')

        # 1) базовые проверки
        if '/' not in img_format or not img_str:
            # ожидали img_format вида "data:image/png", img_str вида "iVBORw0...", но получили что-то другое
            logger.error('[save_diary_meal_image] Wrong image_data',
                         extra={'img_format': img_format, 'img_str': img_str})
            return None

        ext = img_format.split('/')[-1]
        filename = str(uuid4())
        file_data = ContentFile(base64.b64decode(img_str), name='%s.%s' % (filename, ext))

        with Image.open(file_data) as image:
            filename = str(uuid4())
            image_file = put_image_in_memory(image=image, filename=filename)

            return image_file

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v2/diary/{diary_date}/meals/image/{meal_dt}/']
    )
    def meals_images_upsert(request, diary_date, meal_dt):
        """
            Загрузка на сервер фото приема пищи
        """
        meal_image = request.data.get('image')
        image_exif = request.data.get('exif') or {}

        image_exif = clean_exif_data(image_exif)

        # === check request data
        try:
            meal_dt = datetime.datetime.strptime(meal_dt, '%Y-%m-%d_%H:%M:%S')
        except (TypeError, ValueError):
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Произошла ошибка при обновлении изображения для рациона: неверный формат даты.",
                    "simplified_errors": [
                        {"Произошла ошибка при обновлении изображения для рациона: неверный формат даты."}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not meal_image:
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Произошла ошибка при обновлении изображения для рациона: нет данных по фотографии.",
                    "simplified_errors": [
                        {'Произошла ошибка при обновлении изображения для рациона: нет данных по фотографии.'}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        readonly = DiaryMealSet.detect_meal_readonly(user=request.user, diary_date=diary_date)
        if readonly:
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Пищевой дневник за эту дату недоступен для редактирования.",
                    "simplified_errors": [{'Пищевой дневник за эту дату недоступен для редактирования.'}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # === check diary
        try:
            diary = DiaryRecord.objects.get(user=request.user, date=diary_date)
        except DiaryRecord.DoesNotExist:
            raise Http404()

        # === check meal_image
        if meal_image.startswith('http'):
            # Картинку не меняли.
            return DiaryMealSet.meals_get(request=request, diary_date=diary_date)

        # === обновим изображение рациона
        start_time = meal_dt.time()
        start_time_is_next_day = True if diary.date == meal_dt.date() else False
        try:
            dm = DiaryMeal.objects.get(
                diary=diary, start_time=start_time, start_time_is_next_day=start_time_is_next_day,
                meal_type__in=DiaryMeal.MEAL_TYPE_FOODS
            )
        except DiaryMeal.DoesNotExist:
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Произошла ошибка при сохранении изображения для рациона: рацион не найден.",
                    "simplified_errors": [
                        {'Произошла ошибка при сохранении изображения для рациона: рацион не найден.'}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        dm.img_meta_data = image_exif

        _image_exif_datetime = dm.image_exif_datetime

        if _image_exif_datetime:
            correct_dt = datetime.datetime.strptime(diary_date, '%Y-%m-%d') - datetime.timedelta(days=1)
            correct_dt_next_day = correct_dt + datetime.timedelta(days=1, hours=6)
            if correct_dt <= _image_exif_datetime <= correct_dt_next_day:
                if correct_dt.date() == _image_exif_datetime.date():
                    dm.meal_image_status = DiaryMeal.IMAGE_STATUS_CORRECT
                else:
                    # фото после полуночи разрешены только для УЖИНА и ПЕРЕКУСОВ
                    if dm.meal_type in (DiaryMeal.MEAL_TYPE_DINNER, DiaryMeal.MEAL_TYPE_SNACK):
                        dm.meal_image_status = DiaryMeal.IMAGE_STATUS_CORRECT
                        # не выставялем start_time_is_next_day, так как юзер мог поменять время в интерфейсе
                        # dm.start_time_is_next_day = True
                    else:
                        dm.meal_image_status = DiaryMeal.IMAGE_STATUS_FAKE_DATE
                        # new_image = draw_fake_mark(new_image)
            else:
                dm.meal_image_status = DiaryMeal.IMAGE_STATUS_FAKE_DATE
                # new_image = draw_fake_mark(new_image)
        else:
            dm.meal_image_status = DiaryMeal.IMAGE_STATUS_FAKE_NO_DATE
            # new_image = draw_fake_mark(new_image)

        # Пришел blob новой картинки.
        new_image = DiaryMealSet.save_diary_meal_image(request.user, meal_image)

        if not new_image:
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Произошла ошибка при обработке изображения.",
                    "simplified_errors": [{"Произошла ошибка при обработке изображения."}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # удалим изображения, если необходимо
        if dm.meal_image:
            dm.meal_image.delete()

        # сохраним данные
        dm.meal_image = new_image
        dm.save()

        return DiaryMealSet.meals_get(request=request, diary_date=diary_date)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['DELETE /v2/diary/{diary_date}/meals/image/{meal_dt}/']
    )
    def meals_images_delete(request, diary_date, meal_dt):
        """
            Удаление фото приема пищи
        """
        try:
            meal_dt = datetime.datetime.strptime(meal_dt, '%Y-%m-%d_%H:%M:%S')
        except (TypeError, ValueError):
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Произошла ошибка при удалении изображения для рациона: неверный формат даты.",
                    "simplified_errors": [
                        {'Произошла ошибка при удалении изображения для рациона: неверный формат даты.'}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # === check diary
        try:
            diary = DiaryRecord.objects.get(user=request.user, date=diary_date)
        except DiaryRecord.DoesNotExist:
            raise Http404()

        start_time = meal_dt.time()
        start_time_is_next_day = True if diary.date == meal_dt.date() else False
        try:
            dm = DiaryMeal.objects.get(
                diary=diary, start_time=start_time, start_time_is_next_day=start_time_is_next_day
            )
        except DiaryMeal.DoesNotExist:
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Произошла ошибка при удалении изображения для рациона: рацион не найден.",
                    "simplified_errors": [{'Произошла ошибка при удалении изображения для рациона: рацион не найден.'}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # удалим изображения
        if dm.meal_image:
            dm.meal_image.delete()

        return DiaryMealSet.meals_get(request=request, diary_date=diary_date)
