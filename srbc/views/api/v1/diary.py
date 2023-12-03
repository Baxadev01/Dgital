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
from rest_framework.decorators import permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from swagger_docs import swagger_docs
from content.models import TGNotificationTemplate
from content.utils import store_dialogue_reply
from srbc.models import (
    DiaryRecord, User, SRBCImage, DiaryMeal, MealComponent, Checkpoint, Profile, MealFault,
    ParticipationGoal, CheckpointPhotos, MealProduct, DiaryMealFault, DiaryRecordAnalysis, 
)
from srbc.permissions import UserCanUseDiary
from srbc.serializers.general import (
    CheckpointPhotoSerializer, SRBCImageSerializer, ParticipationGoalSerializer,
    ParticipationGoalOrderSerializer, DiaryRecordSerializer, DiaryMealDataSerializer,
    DiaryReviewSerializer,
    MealFaultsSerializer, DiaryMealDataAdminSerializer,
    ParticipantDiaryReviewSerializer,
    MealFaultsAdminSerializer,
    MealProductSerializer, DiaryTodaySerializer,
    DiaryTomorrowSerializer, ParticipationGoalStatusSerializer,
)

from srbc.tasks import (collage_build, create_meal_collage,
                        update_collages_image_info, create_or_update_data_image, update_diary_trueweight)
from srbc.utils.meal_recommenation import get_meal_recommendations, get_recommendation_fulfillment
from srbc.utils.meal_containers import get_diary_analysis
from srbc.utils.checkpoint_measurement import collect_image_info
from srbc.utils.diary import get_diary_statistics, diary_meal_analyse, diary_meal_pre_analyse, \
    get_checkpoint_photo_set, get_anlz_mode
from srbc.utils.permissions import HasStaffPermission, IsActiveUser, HasExpertiseAccess, check_user_id, IsWaveUser, \
    HasDiaryReadAccess, HasDiaryWriteAccess
from srbc.utils.srbc_image import (
    build_3view_collage, build_compare_collages, put_image_in_memory,
    draw_fake_mark, clean_exif_data, exist_images_to_collage,
)
from srbc.utils.diary_meal_type import update_meal_types
from srbc.utils.personal_recommendation import get_recommendations

from srbc.serializers.task_based import (
    CheckpointMeasurementSerializer, DiaryDataSerializer, DiaryRecordDataSerializer)


logger = logging.getLogger('DIARY_API')

@method_decorator(name='get', decorator=swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/{user_id}/diary/']
    ))
class DiaryRecordViewSet(LoggingMixin, generics.ListAPIView):
    """ Получение дневника пользователя """

    permission_classes = (IsAuthenticated, IsActiveUser)
    queryset = DiaryRecord.objects.all().prefetch_related('meals_data')
    serializer_class = DiaryRecordSerializer

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        if not self.request.user.is_staff:
            if user_id != "%s" % self.request.user.pk:
                raise Http404()

        self.queryset = self.queryset.filter(user__id=user_id)

        try:
            if 'start' in self.request.GET:
                self.queryset = self.queryset.filter(date__gte=DateField().to_python(self.request.GET.get('start')))

            if 'end' in self.request.GET:
                self.queryset = self.queryset.filter(date__lte=DateField().to_python(self.request.GET.get('end')))
        except Exception:
            raise Http404()

        return self.queryset



class DiaryChartView(LoggingMixin, generics.GenericAPIView):
    permission_classes = (IsAuthenticated, IsActiveUser,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/{user_id}/diary/chart/']
    )
    def get(request, user_id):
        """
            Получение данных статистики рациона
        """
        if not request.user.is_staff:
            if int(user_id) != request.user.pk:
                raise Http404()

        data = get_diary_statistics(
            user_id=int(user_id),
            end_date=timezone.now().date() + datetime.timedelta(days=1),
            is_staff=request.user.is_staff
        )

        return Response(data)


class FullPointsDiaryChartView(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser, HasExpertiseAccess,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/{user_id}/diary/chart/full_points/']
    )
    def get_stat(request, user_id):
        """
            Получение данных статистики рациона вместе с пустыми днями
        """
        if not request.user.is_staff:
            if int(user_id) != request.user.pk:
                raise Http404()

        data = get_diary_statistics(
            user_id=int(user_id),
            end_date=timezone.now().date() + datetime.timedelta(days=1),
            is_staff=request.user.is_staff,
            add_empty_days=True
        )

        return Response(data)


class MealFaultSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated,  HasDiaryReadAccess)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/faults/']
    )
    def get_list(request):
        """
            Получение общей статистики действий по накоплению жира у текущего пользователя
        """
        faults = MealFault.objects.filter(is_active=True).order_by('code')

        if not request.user.is_staff:
            faults = faults.filter(is_public=True)

        faults = faults.all()
        # faults = list(faults)

        if request.user.is_staff:
            serialized = MealFaultsAdminSerializer(instance=faults, many=True)
        else:
            serialized = MealFaultsSerializer(instance=faults, many=True)
        return Response(serialized.data)


class DiaryNotReadySet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated,  HasDiaryWriteAccess)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/not-ready/{diary_date}/']
    )
    def get_not_ready_list(request, diary_date):
        """
            Получение записей в дневнике со статусом "Ожидает заполнения"
        """

        today = datetime.date.today()
        allowed_days = request.user.profile.meal_days_allowed_delay or 0
        min_date = today - datetime.timedelta(days=allowed_days)

        # обсудили с Шуром , показываем только даты ДО текущего отправляемого дневника
        dates = DiaryRecord.objects.filter(
            user=request.user,
            date__gte=min_date,
            date__lt=diary_date,
            meal_status=DiaryRecord.MEAL_STATUS_NOT_READY,
            meals_data__meal_type__in=DiaryMeal.MEAL_TYPE_FOODS
        ).order_by('-date').values_list('date').distinct().all()

        return Response(
            # ["%s.%s" % (record[0].day, record[0].month) for record in dates]
            [record[0] for record in dates]
        )


class MealRecommendationsSet(LoggingMixin, APIView):
    permission_classes = (IsAuthenticated, IsActiveUser, IsWaveUser,)
    @swagger_auto_schema(
        **swagger_docs['GET /v1/meals/recommendations/']
    )
    def get(self, request):
        """
            Cписок персонализированных рекомендаций
            На основании рекомендаций (UserNote) составляет рекомендации по приему пищи для пользователя.
        """

        if request.query_params.get('date'):
            try:
                date = datetime.datetime.strptime(request.query_params.get('date'), '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    data={
                        "code": status.HTTP_400_BAD_REQUEST,
                        "status": "error",
                        "message": 'Wrong date format. Must be YYYY-MM-DD'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date = datetime.date.today()

        meal_recommendations = get_meal_recommendations(user_id=request.user.id, reference_date=date)

        return Response(
            meal_recommendations
        )


class DiaryMealSet(LoggingMixin, viewsets.ViewSet):

    def get_permissions(self):
        if self.action in ['meals_get', 'diary_get']:
            return [IsAuthenticated(), HasDiaryReadAccess()]
        else:
            # 'save_diary_meal_image', 'data_upsert', 'meals_upsert', 'meals_images_upsert', 'meals_images_delete'
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
    def detect_data_readonly(user, diary_date):
        MAX_DATA_DELAY = 7
        readonly = False
        # tz = pytz.timezone(user.profile.timezone)
        # today = tz.localize(datetime.datetime.strptime(diary_date, "%Y-%m-%d")).date()
        # Can not edit future values and/or too old values.
        if (timezone.localtime() - datetime.timedelta(days=MAX_DATA_DELAY)).date() > diary_date:
            readonly = True

        if (timezone.localtime() + datetime.timedelta(days=1)).date() < diary_date:
            readonly = True

        return readonly

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/{diary_user}/{diary_date}/']
    )
    def diary_get(request, diary_user, diary_date):
        """
            Получение данных дневника за выбранную дату
        """

        try:
            diary_date = datetime.datetime.strptime(diary_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                data={"code": status.HTTP_400_BAD_REQUEST, "status": "error", "message": 'Invalid date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.is_staff and int(diary_user) != request.user.id:
            return Response(
                data={"code": status.HTTP_403_FORBIDDEN, "status": "error", "message": 'No access to user data'},
                status=status.HTTP_403_FORBIDDEN
            )

        diary_user = User.objects.select_related('profile').get(pk=diary_user)

        if not diary_user:
            return Response(
                data={"code": status.HTTP_404_NOT_FOUND, "status": "error", "message": 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        diary_date_tomorrow = diary_date + datetime.timedelta(days=1)

        # Locking
        # Profile.objects.select_for_update().get(user=diary_user)

        try:
            diary_today = DiaryRecord.objects.get(user=diary_user, date=diary_date)
        except ObjectDoesNotExist:
            diary_today = DiaryRecord(user=diary_user, date=diary_date)

        try:
            diary_tomorrow = DiaryRecord.objects.prefetch_related(
                Prefetch('faults_list', DiaryMealFault.objects.filter(fault__is_public=True).select_related('fault'))
            ).get(user=diary_user, date=diary_date_tomorrow)

            faults_to_show = [f for f in diary_tomorrow.faults_list.all()]
            diary_tomorrow.faults_list.set(faults_to_show)

        except ObjectDoesNotExist:
            diary_tomorrow = DiaryRecord(user=diary_user, date=diary_date_tomorrow)

        day_format = diary_date_tomorrow.strftime('%Y-%m-%d')
        readonly = DiaryMealSet.detect_meal_readonly(user=request.user, diary_date=day_format)

        if not diary_tomorrow.anlz_mode or (
                diary_tomorrow.meal_status == DiaryRecord.MEAL_STATUS_NOT_READY and not readonly):
            diary_tomorrow.anlz_mode = get_anlz_mode(diary_user, diary_date_tomorrow)

        serialized = DiaryTodaySerializer(instance=diary_today).data
        diary_tomorrow = DiaryTomorrowSerializer(instance=diary_tomorrow).data

        serialized.update(diary_tomorrow)

        return Response(serialized)
    

    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/{diary_user}/{diary_date}/meals/']
    )
    def meals_get_admin(self, request, diary_date, diary_user):
        return self.meals_get(request, diary_date, diary_user)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/{diary_date}/meals/']
    )
    def meals_get(request, diary_date, diary_user=None):
        """
            Получение данных о рационе
        """
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
            if diary.id:
                faults_to_show = [f for f in diary.faults_list.filter(fault__is_public=True).all()]
                # logging.info("=" * 60)
                # logging.info(faults_to_show)
                diary.faults_list.set(faults_to_show)
            serialized = DiaryMealDataSerializer(instance=diary)
        else:
            serialized = DiaryMealDataAdminSerializer(instance=diary)
        return Response(serialized.data)


    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/diary/{diary_user}/{diary_date}/meals/']
    )
    def meals_review(request, diary_date, diary_user):
        """
            Обновление данных пользователя из админки. Только Шаги, Сон и Вес
        """
        user = User.objects.select_related('profile').get(pk=diary_user)

        # check incoming data
        if request.data.get('pers_rec_flag', '').upper() == 'NULL':
            return Response(
                data={
                    "code": status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Пожалуйста, выберите статус персональных рекомендаций.",
                    "simplified_errors": [
                        {"Пожалуйста, выберите статус персональных рекомендаций."}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            diary = DiaryRecord.objects.get(user=user, date=diary_date)
        except ObjectDoesNotExist:
            raise Http404()


        fake_fault_codes = []

        # проверяем на авто черную кнопку,
        if request.data.get('fake'):
            if diary.meal_status == DiaryRecord.MEAL_STATUS_FAKE and not diary.meal_reviewed_by:
                return Response(
                    data={
                        "code": status.HTTP_400_BAD_REQUEST,
                        "status": "error",
                        "message": "Пользователь уже сам нажал 'черную кнопку'",
                        "simplified_errors": [
                            {"Пользователь уже сам нажал 'черную кнопку'"}]
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # дополнительно проверим наличие причины
            reasons = ['DATA_COMP_NUTRITION', 'PHOTO_MEAL_EXTRACOMP', 'PHOTO_COMP_MISSING', 'PHOTO_COMP_DIFFERENT']
            faults = request.data.get('faults_list', [])
            fault_codes = [item.get('fault').get('code') for item in faults]

            fake_fault_codes = set(reasons) & set(fault_codes)

            if len(fake_fault_codes) == 0:
                return Response(
                    data={
                        "code": status.HTTP_400_BAD_REQUEST,
                        "status": "error",
                        "message": "Не указаны причины для нажатия 'черной кнопки'",
                        "simplified_errors": [
                            {"Не указаны причины для нажатия 'черной кнопки'"}]
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not diary.is_meal_validated:
                # не знаю актуален ли еще кейс, сделал явный выход , чтобы потом не путаться в ветках
                serialized = DiaryMealDataAdminSerializer(instance=diary)
                return Response(serialized.data)

        data = request.data
        data['pers_req_faults'] = None

        is_pers_req_failed = False
        # модератор сказал, что есть нарушения
        if request.data.get('pers_rec_flag', '').upper() == DiaryRecord.PERS_REC_F:
            is_pers_req_failed = True
            _, rec_faults_list = get_recommendation_fulfillment(diary)

            sent_faults_list = request.data.get('per_req_faults', [])

            data['pers_req_faults'] = sent_faults_list
            data['pers_rec_check_mode'] = DiaryRecord.PERS_REC_CHECK_AUTO

            rec_faults_list = set(rec_faults_list) if rec_faults_list else set()
            sent_faults_list = set(sent_faults_list)

            if rec_faults_list.symmetric_difference(sent_faults_list):
                data['pers_rec_check_mode'] = DiaryRecord.PERS_REC_CHECK_MANUAL
            else:
                data['pers_rec_check_mode'] = DiaryRecord.PERS_REC_CHECK_AUTO

        serialized = DiaryReviewSerializer(diary, data=data)

        if serialized.is_valid():
            is_diary_reviewed = diary.meal_status == 'DONE'
            old_diary_meal_data = {
                "meals": diary.meals,
                "faults": diary.faults,
                "is_overcalory": diary.is_overcalory,
                "is_ooc": diary.is_ooc,
                # "pers_rec_flag": diary.pers_rec_flag,
            }

            serialized.save()
            diary = DiaryRecord.objects.get(user=user, date=diary_date)

            new_diary_meal_data = {
                "meals": diary.meals,
                "faults": diary.faults,
                "is_overcalory": diary.is_overcalory,
                "is_ooc": diary.is_ooc,
                # "pers_rec_flag": diary.pers_rec_flag,
            }

            meal_date = diary.date - datetime.timedelta(days=1)

            if new_diary_meal_data["meals"] or new_diary_meal_data["is_ooc"]:
                diary.meal_status = 'DONE'
            elif not is_diary_reviewed:
                diary.meal_status = 'FEEDBACK'

            if request.user.is_staff and not diary.meal_reviewed_by:
                diary.meal_reviewed_by = request.user

            diary.meal_last_status_date = datetime.datetime.now()
            diary.save(update_fields=['meal_status', 'meal_last_status_date', 'meal_reviewed_by'])

            new_meal_evaluated = new_diary_meal_data['meals'] or new_diary_meal_data['is_ooc']

            if not is_diary_reviewed and diary.user.profile.telegram_id and new_meal_evaluated:

                if new_diary_meal_data['is_ooc']:
                    formula_notification = "День проведен вне концепции"
                else:

                    if is_pers_req_failed:
                        pers_req_failed_text = "\nПерсональные рекомендации не выполнены:"
                        titles = get_recommendations(data['pers_req_faults'])
                        for title in titles:
                            pers_req_failed_text += " " + title + ","

                        pers_req_failed_text = pers_req_failed_text[:-1]

                    formula_notification = "Жиронакопительных действий: %s" \
                        "%s" \
                        "%s" \
                        "\nБаланс рациона: доступно в личном кабинете" % (
                            new_diary_meal_data['faults'],
                            '\nДополнительные продукты: ☑️' if new_diary_meal_data[
                                'is_overcalory'] else '',
                            pers_req_failed_text if is_pers_req_failed else ''
                        )

                diary_link = 'Для просмотра полного описания откройте рацион в личном кабинете: ' \
                    'https://lk.selfreboot.camp/diary/%s/meals/' % diary.date.strftime('%Y-%m-%d')

                post_notification = "Ваш рацион за %s был проанализирован. \n%s\n\n%s" % (
                    meal_date.isoformat(),
                    formula_notification,
                    diary_link,
                )

                msg = DjangoTelegramBot.dispatcher.bot.send_message(
                    chat_id=diary.user.profile.telegram_id,
                    text=post_notification,
                    disable_web_page_preview=True
                )
                store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

            if new_meal_evaluated:
                diary.is_meal_reviewed = True

                # зададим формулу для изображения рациона
                if diary.meal_image:
                    diary.meal_image.meta_data['formula'] = diary.meal_short_formula
                    diary.meal_image.save(update_fields=['meta_data'])

            if request.data.get('fake'):
                if request.user.is_staff and not diary.meal_reviewed_by:
                    diary.meal_reviewed_by = request.user
                diary.is_fake_meals = True
                diary.meal_status = 'FAKE'
                diary.meal_last_status_date = datetime.datetime.now()

            diary.save()

            if diary.meal_status == 'DONE':           
                diary_stat = get_diary_analysis(diary)
                if diary_stat:
                    DiaryRecordAnalysis.objects.update_or_create(
                        diary=diary, defaults={
                            'containers': diary_stat['containers'],
                            'day_stat': diary_stat['day_stat']
                        }
                    )

            if request.data.get('fake'):
                if request.user.is_staff:
                    # отправляем уведомление юзеру
                    try:
                        reasons_text = ''
                        for fault_code in fake_fault_codes:
                            fault = next(item for item in faults if item.get('fault').get('code') == fault_code)

                            meal_id = fault.get('meal_id')
                            component_id = fault.get('meal_component_id')

                            if meal_id:
                                meal = DiaryMeal.objects.filter(pk=meal_id).first()
                                time_text = meal.start_time.strftime("%H:%M")
                            else:
                                component = MealComponent.objects.get(pk=component_id)
                                time_text = component.meal.start_time.strftime("%H:%M")

                            if fault_code == 'DATA_COMP_NUTRITION':
                                reasons_text += "%s %s указаны ошибочные БЖУ \n" % (time_text, component.description)
                            elif fault_code == 'PHOTO_MEAL_EXTRACOMP':
                                reasons_text += "%s %s \n" % (time_text, fault.get('fault').get('comment'))
                            elif fault_code == 'PHOTO_COMP_MISSING':
                                reasons_text += "%s %s %s \n" % (time_text, component.description,
                                                                 fault.get('fault').get('comment'))
                            elif fault_code == 'PHOTO_COMP_DIFFERENT':
                                reasons_text += "%s %s %s \n" % (time_text, component.description,
                                                                 fault.get('fault').get('comment'))

                        tpl = TGNotificationTemplate.objects.get(system_code='fake_meal_notification')
                        url = 'https://lk.selfreboot.camp/diary/%s/meals/' % diary.date

                        text_to_send = tpl.text.replace('DIARY_URL', url)
                        text_to_send = text_to_send.replace('EXCLUDE_REASON', reasons_text)

                        msg = DjangoTelegramBot.dispatcher.bot.send_message(
                            chat_id=diary.user.profile.telegram_id,
                            text=text_to_send,
                            disable_web_page_preview=True
                        )
                        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
                    except TGNotificationTemplate.DoesNotExist:
                        pass
        else:
            return Response(serialized.errors, status.HTTP_400_BAD_REQUEST)

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
        image_exif = {}

        # 1) базовые проверки
        if '/' not in img_format or not img_str:
            # ожидали img_format вида "data:image/png", img_str вида "iVBORw0...", но получили что-то другое
            logger.error('[save_diary_meal_image] Wrong image_data',
                         extra={'img_format': img_format, 'img_str': img_str})
            return None, image_exif

        ext = img_format.split('/')[-1]
        filename = str(uuid4())
        file_data = ContentFile(base64.b64decode(img_str), name='%s.%s' % (filename, ext))

        with Image.open(file_data) as image:
            # w, h = image.size
            #
            # # 2) Если отличие между шириной и высотой более 1% - не принимаем фото
            # percent_diff = abs(w - h) / ((w + h) / 2) * 100
            # percent_diff = round(abs(percent_diff))
            # if percent_diff > 1:
            #     return None, image_exif

            # 3) получаем Exif-данные фото, если они есть
            try:
                image_exif = image._getexif() or {}
            except AttributeError:
                # не у всех типов изображений можно загрузить EXIF таким образом (например, у PNG)
                image_exif = {}

            if not isinstance(image_exif, dict):
                logger.error("Wierd exif: %s" % image_exif)

            exif_data = clean_exif_data(image_exif)

            filename = str(uuid4())
            image_file = put_image_in_memory(image=image, filename=filename)

            return image_file, exif_data

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/diary/{diary_user}/{diary_date}/data/']
    )
    def data_upsert(request, diary_user, diary_date):
        """
            Обновление данных дневника
        """
        try:
            diary_date = datetime.datetime.strptime(diary_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                data={"code": status.HTTP_400_BAD_REQUEST, "status": "error", "message": 'Invalid date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        diary_user_obj = User.objects.get(pk=diary_user)

        if diary_user_obj.id != request.user.id and not request.user.is_staff:
            return Response(
                data={"code": status.HTTP_409_CONFLICT, "status": "error", "message": 'No access to user data'},
                status=status.HTTP_403_FORBIDDEN
            )

        is_dirty = False
        is_weight_dirty = False

        with transaction.atomic():
            # Locking
            Profile.objects.select_for_update().get(user=diary_user_obj)
            try:
                diary = DiaryRecord.objects.select_related('user', 'user__profile').get(
                    user=diary_user_obj, date=diary_date
                )
            except ObjectDoesNotExist:
                diary = DiaryRecord(user=diary_user_obj, date=diary_date)
                # diary.save()

            if DiaryMealSet.detect_data_readonly(diary_user_obj, diary_date) and not request.user.is_staff:
                return Response(
                    data={"code": status.HTTP_409_CONFLICT, "status": "error",
                          "message": 'Data for the date is readonly'},
                    status=status.HTTP_409_CONFLICT)

            data = request.data
            serializer = DiaryDataSerializer(instance=diary, data=data)

            if not serializer.is_valid():
                return Response(
                    data={
                        'code': status.HTTP_400_BAD_REQUEST,
                        "status": "error",
                        "message": "Bad Request",
                        "errors": serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            instance, is_dirty, is_weight_dirty = serializer.save()
            response_data = serializer.data

        # из-за атомика - затычка, нельзся сохранять в самом сериалайзере
        # возможно стоит пересмотреть структуру работы с этим в целом
        if is_dirty:
            if is_weight_dirty:
                update_diary_trueweight.delay(user_id=diary.user.pk, start_from=diary.date)
                update_collages_image_info.delay(diary_record_id=diary.pk)

            create_or_update_data_image.delay(user_id=diary.user.pk, diary_record_id=diary.pk)

        return Response(data=response_data, status=status.HTTP_200_OK)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/diary/{diary_date}/meals/']
    )
    def meals_upsert(request, diary_date):
        """
            Обновление/Создание записи рациона
        """

        with transaction.atomic():
            # Locking
            Profile.objects.select_for_update().get(user=request.user)
            try:
                diary = DiaryRecord.objects.get(
                    user=request.user, date=diary_date
                )
            except ObjectDoesNotExist:
                diary = DiaryRecord(user=request.user, date=diary_date)
                # diary.save()

            readonly = DiaryMealSet.detect_meal_readonly(user=request.user, diary_date=diary_date)

            if request.data.get('verified'):
                # отправка на анализ
                diary.anlz_mode = get_anlz_mode(diary.user, diary.date)
                diary.is_weight_accurate = request.data.get('weight_accurate', True)

                # обязательно должно быть задано время ухода ко сну
                if not diary.bed_time:
                    return Response(
                        data={
                            "code": 400,
                            "status": "error",
                            "message": "Не указано время отхода ко сну"
                        },
                        status=400
                    )

                tz = pytz.timezone(request.user.profile.timezone)
                today = tz.localize(datetime.datetime.strptime(diary_date, "%Y-%m-%d"))

                # === "К каждому приему пищи требуется фото" - для участников, которых цифрует команда

                _dm = DiaryMeal.objects.filter(
                    diary=diary, meal_image__exact=''
                ).exclude(
                    meal_type__in=[
                        DiaryMeal.MEAL_TYPE_SLEEP,
                        DiaryMeal.MEAL_TYPE_HUNGER,
                        DiaryMeal.MEAL_TYPE_BLOOD_GLUCOSE
                    ]
                ).first()

                if _dm:
                    return Response(
                        data={
                            "code": 400,
                            "status": "error",
                            "message": "%s: отсутствует фото" % _dm.meal_type
                        },
                        status=400
                    )

                # сразу сделаем все проверки для возврата 400 респонса
                if not exist_images_to_collage(diary):
                    return Response(
                        data={
                            "code": 400,
                            "status": "error",
                            "message": "Необходимо загрузить хотя бы одно фото еды."
                        },
                        status=400
                    )
                elif not timezone.localtime() - datetime.timedelta(hours=3) > today:
                    return Response(
                        data={
                            "code": 400,
                            "status": "error",
                            "message": "Слишком рано. "
                            "Отправка рациона возможна только на следующий день после даты рациона.",
                        },
                        status=400
                    )

                else:
                    diary.is_meal_validated = True
                    diary.meal_validation_date = timezone.localtime()
                    diary.meal_status = 'PENDING'

                    diary_meal_pre_analyse(diary)
                    diary_meal_analyse(diary)

                    diary.save()

                    create_meal_collage.delay(diary.id)

            elif not readonly:
                if request.data.get('fake'):
                    if diary.is_meal_validated:
                        diary.meal_status = 'FAKE'
                        diary.is_fake_meals = True
                        # убрали в рамках задачи 1677
                        # if diary.meal_image:
                        #     diary.meal_image.is_published = False
                        #     diary.meal_image.save(update_fields=['is_published'])

                        # обнулить фолты, и кто
                        diary.meal_reviewed_by = None
                        diary.save()

                        DiaryMealFault.objects.filter(diary_record=diary).delete()
                else:
                    logger.info("Meals data sent for %s by user #%s: %s" % (diary_date, request.user.pk, request.data))

                    serialized = DiaryMealDataSerializer(instance=diary, data=request.data)
                    if not diary.is_meal_validated:
                        if serialized.is_valid():
                            serialized.save()
                            diary.meal_status = 'NOT_READY'
                            diary.last_meal_updated = timezone.now()
                            diary.save(update_fields=['meal_status', 'last_meal_updated', ])
                        else:
                            return Response(serialized.errors, status.HTTP_400_BAD_REQUEST)

        return DiaryMealSet.meals_get(request=request, diary_date=diary_date)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/diary/{diary_date}/meals/image/{meal_dt}/']
    )
    def meals_images_upsert(request, diary_date, meal_dt):
        """
            Сохранение на сервер фото приема пищи
        """
        meal_image = request.data.get('meal_image')

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
        start_time_is_next_day = (diary.date == meal_dt.date())

        try:
            dm = DiaryMeal.objects.get(
                diary=diary, start_time=start_time, start_time_is_next_day=start_time_is_next_day
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

        # Пришел blob новой картинки.
        new_image, image_exif = DiaryMealSet.save_diary_meal_image(request.user, meal_image)

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

        # удалим изображения, если необходимо
        if dm.meal_image:
            dm.meal_image.delete()

        # сохраним данные
        dm.meal_image = new_image
        dm.save()

        return DiaryMealSet.meals_get(request=request, diary_date=diary_date)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['DELETE /v1/diary/{diary_date}/meals/image/{meal_dt}/']
    )
    def meals_images_delete(request, diary_date, meal_dt):
        """
            Удаление изображения еды
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
                    "message": "Произошла ошибка при удалении изображения для рациона: рацион не найден.",
                    "simplified_errors": [{'Произошла ошибка при удалении изображения для рациона: рацион не найден.'}]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # удалим изображения
        if dm.meal_image:
            dm.meal_image.delete()

        return DiaryMealSet.meals_get(request=request, diary_date=diary_date)


class CheckpointPhotoSet(LoggingMixin, viewsets.ViewSet):

    def get_permissions(self):
        if self.action in ['photos_get']:
            return [IsAuthenticated(), IsActiveUser()]
        else:
            #'photos_crop', 'collage_build'
            # elif self.action in ['photos_crop', 'collage_build']:
            return [IsAuthenticated(), HasExpertiseAccess(), IsActiveUser()]

    @swagger_auto_schema(
        **swagger_docs['GET /v1/checkpoints/{user_id}/photos/']
    )
    def photos_get_admin(self, request, user_id):
        return self.photos_get(request, user_id)


    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/checkpoints/photos/']
    )
    def photos_get(request, user_id=None):
        """
            Получение всех контрольных фото (для всех - только себя, для staff - любые)
        """
        if not user_id:
            user_id = request.user.pk
        else:
            if not request.user.is_staff:
                if int(user_id) != request.user.pk:
                    raise Http404()

        photo_data = get_checkpoint_photo_set(user_id)

        return Response(photo_data)

    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/checkpoints/{user_id}/photos/']
    )
    def photos_crop_admin(self, request, user_id):
        return self.photos_crop(request, user_id)


    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/checkpoints/photos/']
    )
    def photos_crop(request, user_id=None):
        """
            Обрезать фотографии (для всех - только себя, для staff - любые)
        """
        if not user_id:
            user_id = request.user.pk
        else:
            if not request.user.is_staff:
                if int(user_id) != request.user.pk:
                    raise Http404()

        if not request.data.get('id'):
            raise Http404()

        photoset = CheckpointPhotos.objects.filter(user_id=user_id, pk=request.data.get('id')).first()

        if not photoset:
            raise Http404()

        if 'crop_meta' not in request.data:
            return HttpResponseBadRequest()

        if photoset.crop_meta is None:
            photoset.crop_meta = dict()

        for i in ['front', 'side', 'rear']:
            if i in request.data['crop_meta']:
                view_meta = request.data['crop_meta'][i]
                viem_crop_data = view_meta.get('crop', {})
                photoset.crop_meta[i] = {
                    "angle": view_meta.get('angle'),
                    "eyeline": view_meta.get('eyeline'),
                    "kneeline": view_meta.get('kneeline'),
                    "crop": {
                        "top": viem_crop_data.get('top'),
                        "left": viem_crop_data.get('left'),
                        "width": viem_crop_data.get('width'),
                        "height": viem_crop_data.get('height'),
                    }
                }

        photoset.save(update_fields=['crop_meta'])

        return CheckpointPhotoSet.photos_get(request, user_id)
    
    
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/checkpoints/{user_id}/photos/']
    )
    def collage_build_admin(self, request, user_id):
        return self.collage_build(request, user_id)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/checkpoints/photos/']
    )
    def collage_build(request, user_id=None):
        """
            Сделать коллаж (для всех - только себя, для staff - любые)
        """
        if not user_id:
            user_id = request.user.pk
        else:
            if not request.user.is_staff:
                if int(user_id) != request.user.pk:
                    raise Http404()

        if not request.data.get('id'):
            raise Http404()

        photoset = CheckpointPhotos.objects.filter(user_id=user_id, pk=request.data.get('id')).first()

        if not photoset:
            raise Http404()

        # добавим сюда валидацию, чтобы не сыпалась в таске
        photoset_base = CheckpointPhotos.objects.filter(user_id=user_id, status='APPROVED').order_by('date').first()

        crop_meta = photoset.crop_meta
        if 'front' not in crop_meta or 'side' not in crop_meta or 'rear' not in crop_meta:
            return HttpResponseBadRequest()

        base_crop_meta = photoset_base.crop_meta
        if 'front' not in base_crop_meta or 'side' not in base_crop_meta or 'rear' not in base_crop_meta:
            return HttpResponseBadRequest()

        task = collage_build.delay(user_id=user_id, photoset_id=photoset.pk)
        return Response({"task_id": task.id})


class CheckPointMeasurementSet(LoggingMixin, viewsets.ViewSet):

    def get_permissions(self):
        if self.action in ['get_measurements', 'get_measurement']:
            return [IsAuthenticated(), IsActiveUser()]
        else:
         # 'create_measurement', 'update_measurement', 'delete_measurement'
            return [IsAuthenticated(), HasExpertiseAccess(), IsActiveUser()]

    @staticmethod
    def _check_request_date(date):
        """ Проверяет формат даты, переданной в запросе.

        :param date:
        :type date: str
        :return: объекты даты или None в случае ошибки
        :rtype: datetime.date | None
        """
        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
        else:
            return date
        
    @swagger_auto_schema(
        **swagger_docs['GET /v1/checkpoints/{user_id}/measurements/']
    )
    def get_measurements_admin(self, request, user_id):
        return self.get_measurements(request, user_id)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/checkpoints/measurements/']
    )
    def get_measurements(request, user_id=None):
        """ Отдать данные по всем замерам пользователя (для всех - только себя, для staff - любые).

        Коды ответов:
        200 - Данные всех чекпоинтов пользователя
        403 - Не хватает прав на выполнение запроса

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        :param user_id: идентификатор пользователя
        :type user_id: str
        """
        user_id = check_user_id(request, user_id)
        if user_id is None:
            return HttpResponseForbidden()  # 403

        checkpoints = list(Checkpoint.objects.filter(user_id=user_id).order_by('date'))
        checkpoints = [CheckpointMeasurementSerializer(instance=i).data for i in checkpoints]

        return Response({"checkpoints": checkpoints})
    

    @swagger_auto_schema(
        **swagger_docs['GET /v1/checkpoints/{user_id}/measurements/{date}/']
    )
    def get_measurement_admin(self, request, user_id):
        return self.get_measurement(request, user_id)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/checkpoints/measurements/{date}/']
    )
    def get_measurement(request, date, user_id=None):
        """ Отдать данные чекпоинта за указанную дату. (для пользователя - только для себя, у админа - чекпойнт для любого пользователя)

        Коды ответов:
        200 - Данные чекпоинта за указанную дату
        400 - Неверный формат даты в запросе
        403 - Не хватает прав на выполнение запроса
        404 - Нет чекпоинта за указанную дату

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        :param date: дата чекпоинта в формате `%Y-%m-%d`
        :type date: str
        :param user_id: идентификатор пользователя
        :type user_id: str
        """
        user_id = check_user_id(request, user_id)
        if user_id is None:
            return HttpResponseForbidden()  # 403

        checkpoint_date = CheckPointMeasurementSet._check_request_date(date=date)
        if checkpoint_date is None:
            return HttpResponseBadRequest()  # 400

        checkpoint = Checkpoint.objects.filter(user_id=user_id, date=checkpoint_date).first()

        if checkpoint:
            return Response({"checkpoint": CheckpointMeasurementSerializer(instance=checkpoint).data})
        else:
            raise Http404()
        
    @swagger_auto_schema(
        **swagger_docs['POST /v1/checkpoints/{user_id}/measurements/{date}/']
    )
    def create_measurement_admin(self, request, user_id):
        return self.create_measurement(request, user_id)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['POST /v1/checkpoints/measurements/{date}/']
    )
    def create_measurement(request, date, user_id=None):
        """ Создать чекпоинт за определенную дату (для пользователя - только для себя, у админа - чекпойнт для любого пользователя)

        Коды ответов:
        200 - Данные созданного чекпоинта
        400 - Неверный формат даты в запросе
        403 - Не хватает прав на выполнение запроса
        409 - Чекпоинт за запрошунную дату уже существует

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        :param date: дата чекпоинта в формате `%Y-%m-%d`
        :type date: str
        :param user_id: идентификатор пользователя
        :type user_id: str
        """
        user_id = check_user_id(request, user_id)
        if user_id is None:
            return HttpResponseForbidden()  # 403

        checkpoint_date = CheckPointMeasurementSet._check_request_date(date=date)
        if checkpoint_date is None:
            return HttpResponseBadRequest()  # 400

        conflict_condition = Checkpoint.objects.filter(user_id=user_id, date=checkpoint_date).exists() or \
            Checkpoint.objects.filter(user_id=user_id, is_editable=True).exists()
        if conflict_condition:
            return Response(data={"code": status.HTTP_409_CONFLICT, "status": "error", "message": 'Conflict in create'},
                            status=status.HTTP_409_CONFLICT)
        else:
            checkpoint = Checkpoint(user_id=user_id, date=checkpoint_date)
            checkpoint.save()
            return Response({"checkpoint": CheckpointMeasurementSerializer(instance=checkpoint).data})

    
    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/checkpoints/{user_id}/measurements/{date}/']
    )
    def update_measurement_admin(self, request, user_id):
        return self.update_measurement(request, user_id)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/checkpoints/measurements/{date}/']
    )
    def update_measurement(request, date, user_id=None):
        """ Изменяет данные РЕДАКТИРУЕМОГО чекпоинта. (для пользователя - только для себя, у админа - чекпойнт для любого пользователя)

        Редактируемые поля: "date", "is_editable", поля замеров (measurement_point_X)

        Коды ответов:
        200 - Данные измененного чекпоинта
        400 - Неверный формат даты в запросе
        403 - Не хватает прав на выполнение запроса
        404 - Не найден редактируемый чекпоинт за указанную дату
        409 - Дата, на которую изменяем чекпоинт, уже занята другим чекпоинтом

        :param request:
        :param date: дата чекпоинта в формате `%Y-%m-%d`
        :type date: str
        :param user_id: идентификатор пользователя
        :type user_id: str
        """
        user_id = check_user_id(request, user_id)
        if user_id is None:
            return HttpResponseForbidden()  # 403

        checkpoint_date = CheckPointMeasurementSet._check_request_date(date=date)
        if checkpoint_date is None:
            return HttpResponseBadRequest()  # 400

        checkpoint = Checkpoint.objects.filter(user_id=user_id, date=checkpoint_date, is_editable=True).first()
        if not checkpoint:
            raise Http404()

        # подготовим данные для обновления
        update_data = request.data.copy()

        if update_data.get('date') and update_data.get('date') != date:
            # change date -> check it
            edited_date = CheckPointMeasurementSet._check_request_date(date=update_data['date'])

            if not edited_date:
                # bad date format
                return HttpResponseBadRequest()

            if Checkpoint.objects.filter(user_id=user_id, date=edited_date).exists():
                return Response(
                    data={"code": status.HTTP_409_CONFLICT, "status": "error", "message": 'Checkpoint exists'},
                    status=status.HTTP_409_CONFLICT
                )

            update_data['date'] = edited_date
        else:
            update_data['date'] = checkpoint.date

        # если не передавали is_editable, то он True
        if update_data.get('is_editable') is None:
            update_data['is_editable'] = checkpoint.is_editable

        serialized = CheckpointMeasurementSerializer(checkpoint, data=update_data)
        if serialized.is_valid():
            serialized.save()
            return CheckPointMeasurementSet.get_measurement(
                request=request, date=update_data['date'].strftime('%Y-%m-%d'), user_id=str(user_id)
            )
        else:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Bad Request",
                    "errors": serialized.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    @swagger_auto_schema(
        **swagger_docs['DELETE /v1/checkpoints/{user_id}/measurements/{date}/']
    )
    def delete_measurement_admin(self, request, user_id):
        return self.delete_measurement(request, user_id)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['DELETE /v1/checkpoints/measurements/{date}/']
    )
    def delete_measurement(request, date, user_id=None):
        """ Удалить замер за определенную дату (если он редактируем и is_measurements_done=False).
        (для пользователя - только для себя, у админа - чекпойнт для любого пользователя)

        Коды ответов:
        204 - Чекпоинт за переданную дату успешно удален
        400 - Неверный формат даты в запросе
        403 - Не хватает прав на выполнение запроса
        404 - Не найден редактируемый чекпоинт c is_measurements_done=False за указанную дату

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        :param date: дата измерения в формате `%Y-%m-%d`
        :type date: str
        :param user_id: идентификатор пользователя
        :type user_id: str
        """
        user_id = check_user_id(request, user_id)
        if user_id is None:
            return HttpResponseForbidden()  # 403

        checkpoint_date = CheckPointMeasurementSet._check_request_date(date=date)
        if checkpoint_date is None:
            return HttpResponseBadRequest()  # 400

        checkpoint = Checkpoint.objects.filter(
            user_id=user_id, date=checkpoint_date, is_editable=True, is_measurements_done=False
        ).first()
        if checkpoint:
            checkpoint.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise Http404()


class DiaryRecordSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (HasStaffPermission,)

    @staticmethod
    def data_upsert(request, user_id, diary_date):
        """ Редактирование ежедневных данных участников модераторами (только для staff)

        :param request:
        :param user_id:
        :type user_id: int
        :param diary_date:
        :type diary_date: str
        """
        if not Profile.objects.filter(user_id=user_id).exists():
            return Response(
                data={"code": status.HTTP_404_NOT_FOUND, "status": "error", "message": 'User not exist'},
                status=status.HTTP_404_NOT_FOUND)

        # вроде метод не используется, но добавим сразу и сюда
        with transaction.atomic():
            # Locking
            Profile.objects.select_for_update().get(user_id=user_id)

            diary_record = DiaryRecord.objects.filter(user_id=user_id, date=diary_date). \
                only('user', 'date', 'weight', 'steps').first()
            if not diary_record:
                diary_record = DiaryRecord(user_id=user_id, date=diary_date)
                diary_record.save()

        serializer = DiaryRecordDataSerializer(instance=diary_record, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Bad Request",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class MealProductsSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser, HasDiaryWriteAccess)

    # noinspection SqlNoDataSourceInspection
    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/products/']
    )
    def search(request):
        """
            Получение списка имеющихся продуктов
        """
        q = request.GET.get('q', '')
        q = q.strip()
        if len(q) < 3:
            return Response(
                data=[]
            )

        q = q.upper()

        morph = MorphAnalyzer()
        regex = re.compile('[^А-ЯA-Z]')
        q = regex.sub(' ', q)
        words = q.split()

        if not words:
            return Response(
                data=[]
            )

        subqueries = []
        words_to_search = []
        for _word in words:
            if len(_word) < 3:
                continue
            words_to_search.append(_word)
            word_q = morph.parse(_word)[0].normal_form.upper()
            if len(word_q) > 3:
                words_to_search.append(word_q)

        if not words_to_search:
            return Response(
                data=[]
            )

        for _word in words_to_search:
            subqueries.append(
                """
                select
                    mp.id,
                    mp.title,
                    component_type,
                       case
                           when UPPER(mp.title) like '%(q)s%%%%' then 9000
                           when UPPER(mpa.title) like '%(q)s%%%%' then 9000
                           when UPPER(mp.title) like '%%%% %(q)s%%%%' then 5000 - strpos(UPPER(mp.title), '%(q)s')
                           when UPPER(mpa.title) like '%%%% %(q)s%%%%' then 5000 - strpos(UPPER(mpa.title), '%(q)s')
                           when UPPER(mp.title) like '%%%%%(q)s%%%%' then 2000 - strpos(UPPER(mp.title), '%(q)s')
                           when UPPER(mpa.title) like '%%%%%(q)s%%%%' then 2000 - strpos(UPPER(mpa.title), '%(q)s')
                           else 1
                       end as score,
                    1 as cnt
                from srbc_mealproduct mp left join srbc_mealproductalias mpa ON mp.id = mpa.product_id 
                where   is_verified is True
                    and component_type is NOT NULL
                    and (UPPER(mp.title) like '%%%%%(q)s%%%%' or UPPER(mpa.title) like '%%%%%(q)s%%%%')
                
                """ % {
                    "q": _word,
                }
            )

        subquery = ' UNION '.join(subqueries)

        if len(q) < 5:
            limit = 10
        else:
            if len(subqueries) > 1:
                limit = 10
            else:
                limit = 25

        products = MealProduct.objects.raw(
            """
select id, title, component_type from
(%(query)s) sq
group by id, title, component_type
order by 10000 * sum(cnt) + max(score) DESC, title
limit %(limit)s
            """ % {
                "query": subquery,
                "limit": limit,
            }
        )

        products_serializer = MealProductSerializer(products, many=True)
        return Response(data=products_serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/products/wiki/']
    )
    def check_new(request):
        """
            Получение продукта страницы продукта на Википедии
            (или если он имеется в списке продуктов то выводит имеющийся продукт)
        """
        q = request.GET.get('q', '')
        q = q.strip()
        if not q:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Empty title",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        wikipedia.set_lang('ru')

        try:
            the_page = wikipedia.page(title=q, auto_suggest=False)
        except wikipedia.PageError:
            return Response(
                data={
                    'code': status.HTTP_404_NOT_FOUND,
                    "status": "error",
                    "message": "Product not found in Wikipedia",
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except wikipedia.DisambiguationError:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Disambiguation error",
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Error occured while getting info from Wikipedia",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        response_data = {
            "title": the_page.title
        }

        existing_product = MealProduct.objects.filter(
            is_verified=True, component_type__isnull=False, title__iexact=the_page.title,
        ).first()

        if existing_product:
            products_serializer = MealProductSerializer(existing_product)
            response_data = products_serializer.data
        else:
            response_data['url'] = the_page.url

        return Response(data=response_data, status=status.HTTP_200_OK)


class ParticipationGoalSet(LoggingMixin, viewsets.ViewSet):
    serializer_class = ParticipationGoalSerializer

    def get_permissions(self):
        if self.action in ['get_all', 'set_order']:
            return [IsAuthenticated(), HasDiaryReadAccess()]
        else:
            # self.action in ['add_goal', 'edit_status']:
            return [IsAuthenticated(), HasDiaryWriteAccess()]

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/goals/']
    )
    def get_all(request):
        """ Получения списка по участнику - выводятся все неудаленные, сортируются по полю "сортировка" и по дате. """
        goals = ParticipationGoal.objects.filter(user_id=request.user.id)
        return Response(
            data=ParticipationGoalSerializer(goals, many=True).data
        )

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['POST /v1/goals/']
    )
    def add_goal(request):
        """ Добавления цели (текст)

        :param request:
        """

        serializer = ParticipationGoalSerializer(data=request.data, context={'user': request.user})
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED, data=serializer.data)
        else:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Bad Request",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @staticmethod
    def set_order(request):
        """ Сортировка целей - на вход массив целей с новыми значениями поля "сортировка"
        ([{"id": 1, "ordernum": 10}, ...]), на выходе - результат, аналогичный методу ParticipationGoalSet#get_all

        :param request:
        """
        instances = ParticipationGoal.objects.filter(user=request.user)
        serializer = ParticipationGoalOrderSerializer(data=request.data, instance=instances, many=True)
        if serializer.is_valid():
            serializer.save()
            return ParticipationGoalSet.get_all(request=request)
        else:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Bad Request",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/goals/{goal_id}/']
    )
    def edit_status(request, goal_id):
        """ Редактирование недостигнутой цели.
        Если мы хотим изменить цель – старую помечаем как "неактуальная" (флаг "удаленная"),
        и создается новая цель. Данная логика работает при любом изменении.

        :param request:
        :param goal_id:
        :type goal_id: int
        """

        try:
            instance = ParticipationGoal.objects.filter(user=request.user).get(pk=goal_id)
        except ParticipationGoal.DoesNotExist:
            raise Http404()

        serializer = ParticipationGoalStatusSerializer(data=request.data, instance=instance)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        else:
            return Response(
                data={
                    'code': status.HTTP_400_BAD_REQUEST,
                    "status": "error",
                    "message": "Bad Request",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
