# -*- coding: utf-8 -*-
import datetime
import logging

import pytz
from django.http.response import HttpResponseBadRequest, Http404
from django.utils import timezone
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator

from swagger_docs import swagger_docs
from srbc.models import InstagramImage

from srbc.models import SRBCImage, DiaryRecord
from srbc.models import User
from srbc.serializers.general import InstagramImageSerializer, SRBCImageSerializer, DiaryRecordShortSerializer
from srbc.utils.permissions import IsActiveUser, HasExpertiseAccess, IsWaveUser
from srbc.utils.srbc_image import save_srbc_image

logger = logging.getLogger('IMAGES_API')

DEFAULT_PAGE_SIZE = 24


class MealImageUploadView(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser, IsWaveUser, HasExpertiseAccess,)

    @swagger_auto_schema(
        **swagger_docs['PUT /v1/images/meals/']
    )
    def upload(self, request):
        """
            Сохранение на сервер коллажа рациона
        """

        imageData = request.data.get('image')

        if not imageData:
            return HttpResponseBadRequest()

        meal_date = request.data.get('date')
        if not meal_date:
            return HttpResponseBadRequest()

        tz = pytz.timezone(request.user.profile.timezone)
        work_date = tz.localize(datetime.datetime.strptime(meal_date, "%Y-%m-%d"))

        img_save_result = save_srbc_image(
            user=request.user, image_date=work_date.date(), image_data=imageData, image_type='MEAL'
        )

        if not img_save_result:
            return HttpResponseBadRequest()

        return Response(status=status.HTTP_200_OK)


class SRBCImagesListViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser, IsWaveUser, HasExpertiseAccess,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/{user_id}/images/']
    )
    def list_images(request, user_id):
        """
            Получение списка фотографий пользователя
        """
        queryset = SRBCImage.objects.filter(is_published=True)
        if not request.user.is_staff:
            user_id = request.user.pk
        else:
            user_id = user_id

        queryset = queryset.filter(user_id=user_id).order_by('-date', 'image_type', '-date_added', )

        # print self.request.GET

        if request.GET.get('from'):
            try:
                min_timestamp = datetime.datetime.fromtimestamp(int(request.GET.get('from')), tz=pytz.UTC)
                queryset = queryset.filter(date__gte=min_timestamp)
            except ValueError:
                pass

        if request.GET.get('to'):
            try:
                max_timestamp = datetime.datetime.fromtimestamp(int(request.GET.get('to')), tz=pytz.UTC)
                queryset = queryset.filter(date__lte=max_timestamp)
            except ValueError:
                pass

        if request.GET.get('page') or request.GET.get('page_size'):
            page_num = 1
            page_size = DEFAULT_PAGE_SIZE

            if request.GET.get('page') is not None and request.GET.get('page').isnumeric():
                page_num = int(request.GET.get('page', 1))

            if request.GET.get('page_size') is not None and request.GET.get('page_size').isnumeric():
                page_size = int(request.GET.get('page_size', DEFAULT_PAGE_SIZE))

            offset = (page_num - 1) * page_size
            limit = page_size
            queryset = queryset.all()[offset:offset + limit]
        else:
            queryset = queryset.all()

        serialized = SRBCImageSerializer(instance=queryset, many=True)

        dates_to_fetch = [i.date for i in queryset if i.image_type in ['MEAL', 'DATA']]
        # print dates_to_fetch

        diaries = DiaryRecord.objects.filter(user_id=user_id, date__in=dates_to_fetch).all()

        diaries_dict = dict((str(dr.date), dr) for dr in diaries)
        # print diaries_dict
        # print serialized.data

        response_data = serialized.data
        for img in response_data:
            if img['date'] in diaries_dict:
                dr_data = DiaryRecordShortSerializer(diaries_dict.get(img['date']))
                img['diary'] = dr_data.data

        return Response(response_data)


@method_decorator(name='get', decorator=swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/{user_id}/ig/images/']
    ))
class IGImagesListViewSet(LoggingMixin, generics.ListAPIView):
    """
        Получение списка инстаграм фотографий пользователя
    """
    permission_classes = (IsAuthenticated, IsAdminUser,)

    queryset = InstagramImage.objects.filter(is_deleted=False).all()
    serializer_class = InstagramImageSerializer

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            user_id = self.request.user.pk
        else:
            user_id = self.kwargs['user_id']

        queryset = queryset.filter(user_id=user_id).order_by('-post_date')

        # print self.request.GET

        if self.request.GET.get('from'):
            try:
                min_timestamp = datetime.datetime.fromtimestamp(int(self.request.GET.get('from')), tz=pytz.UTC)
                # print min_timestamp
                queryset = queryset.filter(post_date__gte=min_timestamp)
            except ValueError:
                pass

        if self.request.GET.get('to'):
            try:
                max_timestamp = datetime.datetime.fromtimestamp(int(self.request.GET.get('to')), tz=pytz.UTC)
                # print max_timestamp
                queryset = queryset.filter(post_date__lte=max_timestamp)
            except ValueError:
                pass

        return queryset


class IGImagesSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsAdminUser,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/{user_id}/ig/images/{hashtag}/']
    )
    def get_by_hashtag(request, user_id, hashtag):
        """
            Получение списка инстаграм фотографий пользователя по хештегу
        """
        if not request.user.is_staff:
            user_id = request.user.pk

        queryset = InstagramImage.objects.filter(user_id=user_id, tags__contains=[hashtag]).order_by('-post_date').all()

        serialized = InstagramImageSerializer(instance=queryset, many=True)

        return Response(serialized.data)


class SRBCCustomImagesSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser, IsWaveUser, HasExpertiseAccess,)

    ACCEPTED_IMAGE_TYPES = ['MEDICAL', 'GOALS', 'OTHER']

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['POST /v1/profiles/images/custom/']
    )
    def upload_custom_image(request):
        """ Загрузка кастомной картинки в ленту фотографий.
        Доступны для загрузки тольки эти типы фотографий: MEDICAL, GOALS, OTHER

        Коды ответов:
        201 - Изображение сохранено
        400 - Неверные данные

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        """
        user_id = request.user.pk

        image_data = request.data.get('image')
        image_type = request.data.get('image_type')
        image_info = request.data.get('image_info')

        # базовые проверки
        if not image_data or not image_type or (image_type.upper() not in SRBCCustomImagesSet.ACCEPTED_IMAGE_TYPES):
            return HttpResponseBadRequest()

        if not isinstance(image_data, str) or not isinstance(image_info, str):
            return HttpResponseBadRequest()

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponseBadRequest()

        # Базовые проверки пройдены. Сохраняем изображение.

        image_date = datetime.datetime.strftime(timezone.now(), "%Y-%m-%d")

        new_image = save_srbc_image(
            user=user, image_date=image_date, image_data=image_data, image_type=image_type,
            remove_existing=False, is_published=True
        )

        if not new_image:
            return HttpResponseBadRequest()
        else:
            new_image.image_info = image_info
            new_image.save(update_fields=['image_info'])

        return Response(status=status.HTTP_201_CREATED)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/profiles/images/custom/{image_id}/']
    )
    def edit_custom_image(request, image_id):
        """ Изменяет данные картинки.
        В текущей реализации доступно изменение только подписи к картинке.
        Изменять текст (подпись к картинке) можно в течение часа после загрузки.

        Коды ответов:
        200 - Данные изображения изменены
        400 - Невалидный запрос
        409 - Невозможно изменить текст (доступное время для изменения уже истекло)

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        :param image_id: id кастомного изображения
        :type image_id: str(int)
        """
        user_id = request.user.pk

        image_info = request.data.get('image_info')
        if not isinstance(image_info, str):
            return HttpResponseBadRequest()

        try:
            srbc_image = SRBCImage.objects.filter(user_id=user_id, id=image_id).get()
        except SRBCImage.DoesNotExist:
            raise Http404()

        if not srbc_image.custom_image_is_editable:
            return HttpResponseBadRequest(status=status.HTTP_409_CONFLICT)

        now = timezone.now()
        srbc_image.image_info = image_info
        srbc_image.date_modified = now
        srbc_image.save(update_fields=['image_info', 'date_modified'])

        return Response(status=status.HTTP_200_OK)
