# -*- coding: utf-8 -*-
import json
import logging
from datetime import date, timedelta

from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.utils import timezone
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from content.models import AnalysisTemplate
from content.serializers import AnalysisTemplateSerializer
from srbc.forms import AnalysisAdminForm
from srbc.models import DiaryRecord
from srbc.models import Profile, User, UserBookMark, UserNote
from srbc.serializers.general import UserProfileSerializer, BookmarkToggleSerializer, UserShortSerializer
from srbc.utils.permissions import HasStaffPermission


logger = logging.getLogger('STAFF_API')

class ProfileListViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsAdminUser,)

    @swagger_auto_schema(
        **swagger_docs['GET /v1/profiles/']
    )
    def list(self, request):
        """
            Получение списка пользователей
        """
        queryset = self.get_queryset()
        
        return Response(UserShortSerializer(queryset, many=True).data)

    def get_queryset(self):
        queryset = User.objects.select_related(
            'profile',
            'profile__active_tariff_history__tariff__tariff_group',
            'profile__active_tariff_history__wave',
            'profile__next_tariff_history__tariff__tariff_group',
            'profile__next_tariff_history__wave',
            'application__tariff__tariff_group'
        )

        is_filtered = False
        if self.request.query_params.get('wave'):
            queryset = queryset.filter(profile__active_tariff_history__wave_id=self.request.query_params.get('wave'))
            is_filtered = True

        if self.request.query_params.get('username'):
            queryset = queryset.filter(username__startswith=self.request.query_params.get('username'))
            is_filtered = True

        if not is_filtered:
            queryset = queryset.none()

        queryset = queryset.all()

        return queryset


class BookmarkToggleViewSet(LoggingMixin, generics.UpdateAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = BookmarkToggleSerializer

    @swagger_auto_schema(
        **swagger_docs['PATCH /v1/bookmarks/']
    )
    def patch(self, request, *args, **kwargs):
        """
            Обновление закладки
        """
        super().patch(self, request, *args, **kwargs)

    @swagger_auto_schema(
        **swagger_docs['PUT /v1/bookmarks/']
    )
    def put(self, request, *args, **kwargs):
        """
            Добавление пользователя в закладки
        """
        data = request.data
        if "id" not in data:
            return Response([])

        action = data.get('action')
        if action == 'add':
            exists = UserBookMark.objects.filter(user=request.user, bookmarked_user__pk=data.get('id')).exists()
            if not exists:
                bm = UserBookMark()
                bm.user = request.user
                bm.bookmarked_user = User.objects.get(pk=data.get('id'))
                bm.save()
            return_data = {
                "status": "added"
            }
        else:
            UserBookMark.objects.filter(user=request.user, bookmarked_user__pk=data.get('id')).delete()
            return_data = {
                "status": "removed"
            }

        return Response(return_data)


class AnalysisViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (HasStaffPermission,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/profile/{user_id}/analysis/templates/']
    )
    def get_analysis_templates(request, user_id):
        """
            Получение шаблонов для анализа
        """
        templates = AnalysisTemplate.objects.filter(is_visible=True)
        return Response({"templates": [AnalysisTemplateSerializer(instance=i).data for i in templates]})

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['POST /v1/profile/{user_id}/analysis/add/']
    )
    def add_analysis_recommendation(request, user_id):
        """
            Добавление персональной рекомендации
        """

        try:
            profile = Profile.objects.get(user_id=user_id)
        except Profile.DoesNotExist:
            raise Http404()

        user_note = request.data.get('user_note')
        if not user_note:
            return HttpResponseBadRequest()

        form = AnalysisAdminForm(user_note)
        if form.is_valid():
            data = form.cleaned_data
            data['author'] = request.user
            data['user'] = profile.user
            data['date_added'] = timezone.now()
            data['is_published'] = True
            data['label'] = 'IG'
            data['adjust_fruits'] = data['adjust_fruits'] or 'NO'
            warning_flag = data.pop('alarm', None)
            new_analysis = UserNote(**data)
            new_analysis.save()

            if warning_flag:
                profile.warning_flag = warning_flag
                profile.save(update_fields=['warning_flag'])

        else:
            form_errors = {form[k].label: form[k].errors[0] for k in form.errors}
            return HttpResponseBadRequest(json.dumps({'form_errors': form_errors}))

        return Response({'user_note': new_analysis.id})


class NextMealViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (HasStaffPermission,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/staff/tools/next_meal/']
    )
    def get_next_meal(request):
        """
            Получение следующего рациона для анализа
        """
        analyze_mode = request.GET.get('mode')

        today = date.today()

        user_id = None
        meal_date = None
        next_meal = DiaryRecord.objects.filter(
            Q(meal_last_status_date__lt=timezone.now() - timedelta(minutes=10)) | Q(meal_last_status_date__isnull=True),
            meal_status__in=['PENDING', 'VALIDATION', 'FEEDBACK'],

            user__tariff_history__valid_until__gte=today,
            user__tariff_history__valid_from__lte=today,
            user__tariff_history__is_active=True,

            anlz_mode=analyze_mode
        )

        next_meal = next_meal.order_by('meal_validation_date').first()
        if next_meal:
            user_id = next_meal.user_id
            meal_date = next_meal.date

        return Response(
            {
                "user_id": user_id,
                "meal_date": meal_date,
            }
        )
