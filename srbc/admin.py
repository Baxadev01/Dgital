# -*- coding: utf-8 -*-

import re
from datetime import date, timedelta

import pytz
from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import F, OuterRef, Subquery, Q
from django.http.response import Http404
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timezone import localdate
from django.utils.translation import ugettext_lazy as _
from import_export import resources
from import_export.admin import ExportActionModelAdmin

from content.models import TGChat, TGChatParticipant
from srbc.models import (
    AutoAnalizeFormula, Checkpoint, CheckpointPhotos, DiaryRecord, GTTResult, InstagramImage,
    Invitation, MealFault, MealNoticeTemplate, MealNoticeTemplateCategory, MealProduct,
    MealProductAlias, MealProductTag, Profile, SRBCImage, UserNote, UserReport, Wave, TariffGroup,
    Subscription, Tariff
)
from srbc.tasks import generate_results_report, update_diary_trueweight
from srbc.views.api.v1.analytics import result_notice_gen, set_task_for_report_generation

FILTER_FIELD_NATIVE = 'NATIVE'
FILTER_FIELD_PROFILE_BASED = 'PROFILE_BASED'
FILTER_FIELD_USER_BASED = 'USER_BASED'


class UserFilter(AutocompleteFilter):
    title = 'Пользователи'
    field_name = 'user'


class WaveFilter(AutocompleteFilter):
    title = 'Поток'
    field_name = 'wave'


class NoDeleteModelAdmin(admin.ModelAdmin):
    """
    Родительский класс для запрета удаления объекта через админку
    """

    def get_actions(self, request):
        """
            Предотвращает вывод виджета удаления
        """
        actions = super(NoDeleteModelAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        """
            Предотвращает удаление, возвращая код ошибки 403
        """
        return False


class ReadOnlyModelAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if self.declared_fieldsets:
            return flatten_fieldsets(self.declared_fieldsets)
        else:
            return list(set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]
            ))


class IsInChatListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('in chat')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'in_chat'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        chats = TGChat.objects.filter(is_main=True).order_by('-is_active', '-start_date', '-code')
        return [(c.id, c.code) for c in chats]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        # print self.value()
        chat_to_filter = TGChat.objects.filter(pk=self.value()).first()
        # print chat_to_filter
        if chat_to_filter:
            return queryset.filter(user__in=chat_to_filter.members.all())
        else:
            return queryset


class SubscriptionTypeListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('type')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [('1', 'Stripe'), ('2', 'Apple'), ('3', 'Google'), ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == '1':
            return queryset.filter(stripe_subscription__isnull=False)
        elif self.value() == '2':
            return queryset.filter(apple_subscription__isnull=False)
        elif self.value() == '3':
            return queryset.filter(google_subscription__isnull=False)
        else:
            return queryset


class HasProtocolWarningsFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('нарушения протокола')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'protocol_warning'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """

        return [('1', 'Были'), ('0', 'Не было'), ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        today = date.today()

        members_with_warnings = UserNote.objects.filter(
            label='WTF',
            date_added__gte=F('user__profile__active_tariff_history__valid_until') - timedelta(days=58),
            user__profile__active_tariff_history__isnull=False
        ).values_list('user', flat=True)

        if self.value() == '1':
            return queryset.filter(user__in=members_with_warnings.all())
        elif self.value() == '0':
            return queryset.exclude(user__in=members_with_warnings.all())
        else:
            return queryset


class UserBasedWaveListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('wave')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'wave'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        waves = Wave.objects.order_by('-start_date').all()
        return [(w.id, w.title) for w in waves]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value():

            wave_to_filter = Wave.objects.filter(pk=self.value()).first()

            queryset = queryset.filter(
                user__profile__active_tariff_history__wave=wave_to_filter
            )

        return queryset


class WaveListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('wave')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'wave'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        waves = Wave.objects.order_by('-start_date').all()
        return [(w.id, w.title) for w in waves]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value():

            wave_to_filter = Wave.objects.filter(pk=self.value()).first()

            queryset = queryset.filter(
                profile__active_tariff_history__wave=wave_to_filter
            )

        return queryset


class IsInClubFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('В клубе')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_in_club'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """

        return [('1', 'Да'), ('2', 'Нет'), ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value() == '1':
            return queryset.filter(
                active_tariff_history__isnull=False,
                active_tariff_history__tariff__tariff_group__is_in_club=True
            )
        elif self.value() == '2':
            return queryset.filter(
                Q(active_tariff_history__isnull=True)
                |
                Q(
                    active_tariff_history__tariff__tariff_group__is_in_club=False
                )
            )
        else:
            return queryset


class CommunicationModeFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('communication mode')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'communication_mode'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """

        return [('1', 'Канал'), ('2', 'Чат'), ]

    def queryset(self, request, queryset, field_option=FILTER_FIELD_NATIVE):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if not self.value() in ['1', '2']:
            return queryset
        else:
            value = TariffGroup.COMMUNICATION_MODE_CHANNEL if self.value() == '1' else TariffGroup.COMMUNICATION_MODE_CHAT

            if field_option == FILTER_FIELD_NATIVE:
                return queryset.filter(
                    active_tariff_history__tariff__tariff_group__communication_mode=value
                )
            elif field_option == FILTER_FIELD_PROFILE_BASED:
                return queryset.filter(
                    profile__active_tariff_history__tariff__tariff_group__communication_mode=value
                )
            else:
                return queryset.filter(
                    user__profile__active_tariff_history__tariff__tariff_group__communication_mode=value
                )


class UserBasedCommunicationModeFilter(CommunicationModeFilter):

    def queryset(self, request, queryset):
        return super(UserBasedCommunicationModeFilter, self).queryset(request, queryset, FILTER_FIELD_USER_BASED)


class IsActiveFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Профиль активен')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """

        return [('1', 'Да'), ('2', 'Нет'), ]

    def queryset(self, request, queryset, field_option=FILTER_FIELD_NATIVE):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if not self.value() in ['1', '2']:
            return queryset
        else:
            value = self.value() == '2'

            if field_option == FILTER_FIELD_NATIVE:
                return queryset.filter(
                    active_tariff_history__isnull=value
                )
            elif field_option == FILTER_FIELD_PROFILE_BASED:
                return queryset.filter(
                    profile__active_tariff_history__isnull=value
                )
            else:
                return queryset.filter(
                    user__profile__active_tariff_history__isnull=value
                )


class UserBasedIsActiveFilter(IsActiveFilter):

    def queryset(self, request, queryset):
        return super(UserBasedIsActiveFilter, self).queryset(request, queryset, FILTER_FIELD_USER_BASED)


class ProfileBasedIsActiveFilter(IsActiveFilter):

    def queryset(self, request, queryset):
        return super(ProfileBasedIsActiveFilter, self).queryset(request, queryset, FILTER_FIELD_PROFILE_BASED)


class IsNotInChatListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('not in chat')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'not_in_chat'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        chats = TGChat.objects.filter(is_main=True).order_by('-is_active', '-start_date', '-code')
        return [(c.id, c.code) for c in chats]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        chat_to_filter = TGChat.objects.filter(pk=self.value()).first()
        if chat_to_filter:
            return queryset.exclude(user__in=chat_to_filter.members.all())
        else:
            return queryset


class HasApprovedPhotosFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('has approved photos')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'has_photos'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ('approved', "Есть"),
            ('not_approved', "Нет"),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """

        if self.value():
            approved_photos_users = User.objects.filter(checkpoint_photos__status='APPROVED')
            if self.value() == 'approved':
                return queryset.filter(user__in=approved_photos_users)
            else:
                return queryset.exclude(user__in=approved_photos_users)
        else:
            return queryset


class TechDutyShiftAdmin(admin.ModelAdmin):
    list_display = ['id', 'start_date', 'end_date']


class TechDutyAdmin(admin.ModelAdmin):
    list_display = ['shift', 'techcat', 'user', 'mode']
    list_filter = ['shift', 'techcat', 'user', 'mode']


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    def profile_url(self, obj):
        return format_html(
            "<a href='/admin/srbc/profile/{id}/change/'><i class='glyphicon icon-user'></i>&nbsp;Профиль</a>",
            id=obj.user.profile.pk
        )

    profile_url.short_description = "Profile"

    list_filter = ['user', 'author', 'label', 'is_published', 'date_added']
    raw_id_fields = ['user']
    readonly_fields = ['is_notification_sent', ]
    list_display = ['user', 'author', 'label', 'date_added', 'is_published', 'is_notification_sent', 'profile_url', ]
    search_fields = ['content', ]


@admin.register(Checkpoint)
class CheckpointMeasurementsAdmin(admin.ModelAdmin):
    def profile_url(self, obj):
        return format_html(
            "<a href='/admin/srbc/profile/{id}/change/'><i class='glyphicon icon-user'></i>&nbsp;Профиль</a>",
            id=obj.user.profile.pk
        )

    profile_url.short_description = "Profile"

    list_filter = ['is_editable', 'date', 'is_measurements_done']
    raw_id_fields = ['user']
    list_display = ['user', 'date', 'is_editable', 'is_measurements_done', 'profile_url', ]
    search_fields = ['=user__pk', '=user__username']

    readonly_fields = ['is_measurements_done', 'measurement_point_01', 'measurement_point_02', 'measurement_point_03',
                       'measurement_point_04', 'measurement_point_05', 'measurement_point_06', 'measurement_point_07',
                       'measurement_point_08', 'measurement_point_09', 'measurement_point_10', 'measurement_point_11',
                       'measurement_point_12', 'measurement_point_13', 'measurement_point_14', 'measurement_point_15',
                       'measurement_point_16', ]


@admin.register(GTTResult)
class GTTResultAdmin(admin.ModelAdmin):
    def profile_url(self, obj):
        return format_html(
            "<a href='/admin/srbc/profile/{id}/change/'><i class='glyphicon icon-user'></i>&nbsp;Профиль</a>",
            id=obj.user.profile.pk
        )

    profile_url.short_description = "Profile"

    def usernote_url(self, obj):
        return format_html(
            "<a href='/admin/srbc/usernote/{id}/change/'><i class='glyphicon icon-certificate'></i>&nbsp;Заметка</a>",
            id=obj.user_note.pk
        )

    usernote_url.short_description = "Заметка"

    def last_photos(self, obj):
        return ''

    def starting_image_tag(self, obj):
        photo = obj.user.photo_stream.filter(image_type='CHECKPOINT_PHOTO').order_by('-date').first()
        return format_html('<img src="{url}" />', url=photo.image.url)

    def last_face_image_tag(self, obj):
        photo = obj.user.photo_stream.filter(
            image_type='CHECKPOINT_PHOTO_FRONT', date__lte=obj.date).order_by('-date').first()
        return format_html('<img src="{url}" />', url=photo.image.url)

    def last_side_image_tag(self, obj):
        photo = obj.user.photo_stream.filter(
            image_type='CHECKPOINT_PHOTO_SIDE', date__lte=obj.date).order_by('-date').first()
        return format_html('<img src="{url}" />', url=photo.image.url)

    def last_rear_image_tag(self, obj):
        photo = obj.user.photo_stream.filter(
            image_type='CHECKPOINT_PHOTO_REAR', date__lte=obj.date).order_by('-date').first()
        return format_html('<img src="{url}" />', url=photo.image.url)

    starting_image_tag.short_description = "Стартовые фото"
    last_face_image_tag.short_description = "Последние фото. Анфас."
    last_side_image_tag.short_description = "Последние фото. Профиль."
    last_rear_image_tag.short_description = "Последние фото. Спина."

    list_filter = [UserFilter, 'date', 'is_reviewed']
    raw_id_fields = ['user']
    fields = (
        'user',
        'profile_url',
        'date',
        'glucose_unit',
        'status',
        'glucose_express',
        'glucose_0',
        'insulin_0',
        'glucose_60',
        'insulin_60',
        'glucose_120',
        'insulin_120',
        'homa_index',
        'medical_resolution',
        'medical_comment',
        'image_1',
        'image_2',
        'image_3',
        'starting_image_tag',
        'last_face_image_tag',
        'last_side_image_tag',
        'last_rear_image_tag',
        'usernote_url',
    )
    readonly_fields = [
        'profile_url', 'homa_index', 'date_added',
        'usernote_url',
        'starting_image_tag',
        'last_face_image_tag',
        'last_side_image_tag',
        'last_rear_image_tag',
    ]
    list_display = ['id', 'user', 'date', 'homa_index', 'status', 'profile_url', ]
    search_fields = ['=user__pk', ]

    class Media:
        pass


@admin.register(Wave)
class WaveAdmin(NoDeleteModelAdmin):
    list_display = ['id', 'title', 'start_date', 'is_in_club', 'is_archived', ]
    actions = []
    search_fields = ['=id', 'title']
    list_filter = ['is_in_club', ]
    raw_id_fields = ['starting_chat', ]


def update_trueweight(modeladmin, request, queryset):
    for profile in queryset:
        update_diary_trueweight.delay(user_id=profile.user.pk)


def deactivate_user(modeladmin, request, queryset):
    for profile in queryset:
        profile.deactivate()


def request_ig_update(modeladmin, request, queryset):
    queryset.update(instagram_update_required=True)


def promote_next_chat(modeladmin, request, queryset):
    for profile in queryset:
        user_last_chat = TGChatParticipant.objects.filter(user=profile.user, chat__is_main=True,
                                                          chat__chat_type=profile.communication_mode).order_by(
            '-chat__start_date').first()
        if not user_last_chat:
            continue

        if not user_last_chat.chat.next_chat:
            continue

        new_chat_user = TGChatParticipant()
        new_chat_user.user = profile.user
        new_chat_user.chat = user_last_chat.chat.next_chat
        new_chat_user.save()


def analyze_stat_gen(modeladmin, request, queryset):
    today = timezone.now()
    last_monday = today - timedelta(days=(today.weekday() + 1) % 7 + 6)
    for profile in queryset:
        user = profile.user
        notice_exists = UserNote.objects.filter(user=user, label='STAT', date_added__gte=last_monday).exists()
        if notice_exists:
            continue

        new_notice = UserNote()
        new_notice.label = 'STAT'
        new_notice.user = user
        new_notice.date_added = today - timedelta(days=(today.weekday() + 1) % 7 - 1)
        new_notice.author = request.user
        new_notice.is_published = True
        new_notice.content = result_notice_gen(user)
        new_notice.save()


def generate_user_reports(modeladmin, request, queryset):
    """Создает пользовательский отчеты за текущий день"""
    for profile in queryset:
        set_task_for_report_generation(user=profile.user, force=True)


def generate_user_reports_wo_pdf(modeladmin, request, queryset):
    """Создает пользовательские отчеты, у которых нет pdf"""
    for profile in queryset:
        for report in UserReport.objects.filter(user_id=profile.user_id, pdf_file__isnull=True).only('id'):
            generate_results_report.delay(report_id=report.id)


def pdf_report_gen(modeladmin, request, queryset):
    queue_count = 0
    for profile in queryset:
        tz = pytz.timezone(profile.timezone)
        today = localdate(timezone=tz)
        report_exists = UserReport.objects.filter(user_id=profile.user_id, date=today).exists()
        if report_exists:
            continue

        report = UserReport(
            date=today,
            user=profile.user
        )

        report.save()
        # ставим задачу на подсчет отчета
        generate_results_report.delay(report_id=report.id)
        queue_count += 1

    messages.success(
        request,
        "PDF report was generated for %s user%s" % (
            queue_count,
            '' if queue_count == 1 else 's'
        )
    )


def get_profile_ids(modeladmin, request, queryset):
    ids = queryset.values_list('user_id', flat=True)

    messages.success(
        request,
        "User IDs: %s" % ', '.join(['%s' % i for i in ids])
    )


update_trueweight.short_description = "Recalculate TrueWeight"
deactivate_user.short_description = "Deactivate User"
request_ig_update.short_description = "Queue up Instagram update"
promote_next_chat.short_description = "Promote to the next chat/channel"
generate_user_reports.short_description = "Generate User Reports"
generate_user_reports_wo_pdf.short_description = "Fix User Reports w/o PDF"
# analyze_stat_gen.short_description = "Stat notice generation"
pdf_report_gen.short_description = "PDF report generation"
get_profile_ids.short_description = "Get Profile IDs"


@admin.register(Profile)
class ProfileAdmin(NoDeleteModelAdmin):
    def get_queryset(self, request):
        last_weight_subq = DiaryRecord.objects.filter(
            user=OuterRef('user'),
            weight__isnull=False
        ).order_by('-date')

        last_meal_subq = DiaryRecord.objects.filter(
            user=OuterRef('user'),
            is_meal_validated=True
        ).order_by('-date')

        qs = super(ProfileAdmin, self).get_queryset(request)
        qs = qs.annotate(
            last_weight=Subquery(last_weight_subq.values('date')[:1]),
            last_meals=Subquery(last_meal_subq.values('date')[:1])
        )

        qs = qs.select_related('user')
        return qs

    def days_no_weight(self, obj):
        if not obj.last_weight:
            return None

        return (date.today() - obj.last_weight).days

    days_no_weight.short_description = "Дней без веса"

    def days_no_meals(self, obj):
        if not obj.last_meals:
            return None

        return (date.today() - obj.last_meals).days

    days_no_meals.short_description = "Дней без рационов"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tariff_next":
            kwargs["queryset"] = Tariff.objects.filter(is_archived=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = [
        'user_id', 'user',
        'wave',
        'group_leader',
        'days_no_weight', 'days_no_meals',
        'is_active', 'is_in_club', 'valid_until',
    ]
    raw_id_fields = ['user']
    actions = [
        update_trueweight,
        request_ig_update,
        deactivate_user,
        promote_next_chat,
        # analyze_stat_gen,
        pdf_report_gen,
        get_profile_ids,
        generate_user_reports,
        generate_user_reports_wo_pdf
    ]

    exclude = [
        'instagram_link_code', 'visibility', 'widgets_display', 'mifit_last_sync', 'mifit_id',
        'tracker_brand', 'deleted_wave', 'deleted_tariff', 'deleted_valid_until', 'deleted_is_active',
        'deleted_communication_mode', 'tariff_valid_from', 'tariff_valid_until',
    ]
    readonly_fields = ['agreement_signed_date', 'tariff', 'wave', 'valid_until', 
                    'communication_mode', 'is_active', 'active_tariff_history', 'next_tariff_history']

    search_fields = ['=user__id', 'user__username']
    list_filter = [
        # WaveFilter,
        IsActiveFilter,
        IsInClubFilter,
        'group_leader',
        'meal_analyze_mode',
        IsInChatListFilter,
        IsNotInChatListFilter,
        HasApprovedPhotosFilter,
        HasProtocolWarningsFilter,
        # 'visibility',
        CommunicationModeFilter
    ]
    # suit_list_filter_horizontal = ['wave', 'in_chat', 'not_in_chat']

    class Media:
        pass


class DiaryRecordAdmin(NoDeleteModelAdmin):
    list_display = ['id', 'user', 'date', 'weight', 'trueweight', 'steps', 'meals', 'faults']
    fields = ['user', 'date', 'steps', 'sleep', 'weight', 'meals', 'faults']
    actions = []
    search_fields = ['=id', 'user']

    readonly_fields = ['weight', ]


class InvitationCodeExport(resources.ModelResource):
    class Meta:
        model = Invitation
        fields = (
            'code',
        )


@admin.register(Invitation)
class InvitationAdmin(ExportActionModelAdmin):
    resource_class = InvitationCodeExport

    list_display = ['id', 'applied_by', 'applied_at', 'expiring_at', 'wave']
    list_filter = ['is_applied', 'wave', ]
    search_fields = ['=applied_by__pk', '=code']


class UserChatInline(admin.TabularInline):
    verbose_name_plural = "Доступ к чатам"
    model = TGChatParticipant
    extra = 1
    raw_id_fields = ['chat']


admin.site.unregister(User)


@admin.register(User)
class SRBCUserAdmin(UserAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields

        raise Http404()

    def profile_url(self, obj):
        return format_html(
            "<a href='/admin/srbc/profile/{id}/change/'>"
            "<i class='glyphicon icon-{icon}-sign'></i>&nbsp;Профиль"
            "</a>",
            id=obj.profile.pk,
            icon='ok' if obj.profile.is_active else 'remove'
        )

    profile_url.short_description = "Profile"

    def application_url(self, obj):
        if obj.application:
            return format_html(
                "<a href='/admin/crm/application/{id}/change/'>"
                "<i class='glyphicon icon-{icon}-sign'></i>&nbsp;Анкета"
                "</a>",
                id=obj.application.pk,
                icon='ok' if obj.application.is_approved else 'question'
            )
        else:
            return None

    application_url.short_description = "Application"

    def wave_title(self, obj):
        return obj.profile.wave.title if obj.profile.wave else None

    wave_title.short_description = "Wave"

    list_display = ('id',) + UserAdmin.list_display + ('profile_url', 'application_url', 'wave_title')
    search_fields = UserAdmin.search_fields + ('profile__instagram', '=id', 'username')
    list_filter = UserAdmin.list_filter + (
        ProfileBasedIsActiveFilter,
        'application__is_approved',
        WaveListFilter,
    )

    readonly_fields = UserAdmin.readonly_fields + ('profile_url', 'application_url',)

    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'profile_url', 'application_url',),
        }),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    inlines = (UserChatInline,)


@admin.register(AutoAnalizeFormula)
class AutoAnalizeFormulaAdmin(admin.ModelAdmin):
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(AutoAnalizeFormulaAdmin, self).get_search_results(request, queryset, search_term)
        search_term_regex = search_term
        if re.search('^[+=*-][0-5*]{5}$', search_term_regex):
            search_term_regex = search_term_regex.replace("+", "\+")
            search_term_regex = search_term_regex.replace("*", ".")
            queryset |= self.model.objects.filter(code__iregex=search_term_regex)

        return queryset, use_distinct

    list_display = ['code', 'comment', 'attention_required', ]
    search_fields = ['code']


@admin.register(InstagramImage)
class InstagramImageAdmin(admin.ModelAdmin):
    def image_tag(self, obj):
        return format_html('<img src="{url}" />', url=obj.image.url)

    image_tag.short_description = "Image"

    raw_id_fields = ['user']

    list_display = ['id', 'user', 'post_date', 'image', 'post_text', 'role', ]

    list_filter = ['role', ]

    search_fields = ['=user__id']

    readonly_fields = ['user', 'post_date', 'image', 'post_text', 'role']
    fields = ['user', 'post_date', 'image', 'post_text', 'role']


@admin.register(SRBCImage)
class SRBCImageAdmin(NoDeleteModelAdmin):
    def image_tag(self, obj):
        return format_html('<img src="{url}" />', url=obj.image.url)

    image_tag.short_description = "Image"

    raw_id_fields = ['user']

    list_display = ['id', 'user', 'date', 'image_type', 'date_added', 'date_modified', ]

    list_filter = ['image_type', ]

    search_fields = ['user__username', '=id', '=user__id']

    readonly_fields = ['image_tag']


@admin.register(Subscription)
class SubscriptionAdmin(NoDeleteModelAdmin):
    def subscription_type(self, obj):
        if obj.stripe_subscription:
            return 'Stripe'
        elif obj.apple_subscription:
            return 'Apple'
        elif obj.google_subscription:
            return 'Google'
        else:
            return ''

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user', 'tariff', 'status', 'stripe_subscription', 'apple_subscription', 'google_subscription', 'yandex_subscription']
        else:
            return []

    subscription_type.short_description = "Type"
    list_display = ['user_id', 'user', 'tariff', 'status', 'subscription_type']

    autocomplete_fields = ['tariff', 'user', ]
    search_fields = ['=user__id', '=user__username', ]

    list_filter = ['status', SubscriptionTypeListFilter]


@admin.register(CheckpointPhotos)
class CheckpointAdmin(NoDeleteModelAdmin):

    def get_preview_image(self, img_url):
        return format_html('<img style="max-height:70vh; max-width:70vw" src="{url}" />', url=img_url)

    def front_image_tag(self, obj):
        return self.get_preview_image(obj.front_image.url)

    def side_image_tag(self, obj):
        return self.get_preview_image(obj.side_image.url)

    def rear_image_tag(self, obj):
        return self.get_preview_image(obj.rear_image.url)

    def wave_title(self, obj):
        return obj.user.profile.wave.title if obj.user.profile.wave else 'Без потока'

    front_image_tag.short_description = 'Front'
    front_image_tag.allow_tags = True

    side_image_tag.short_description = 'Side'
    side_image_tag.allow_tags = True

    rear_image_tag.short_description = 'Rear'
    rear_image_tag.allow_tags = True

    raw_id_fields = ['user']

    list_display = ['user', 'date', 'status', 'wave_title']
    list_filter = ['status',
                   UserBasedWaveListFilter,
                   UserBasedIsActiveFilter,
                   UserBasedCommunicationModeFilter,

                   ]
    fields = (
        'user', 'date', 'status', 'rejection_reasons', 'rejection_comment',
        'front_image_tag', 'front_image',
        'side_image_tag', 'side_image',
        'rear_image_tag', 'rear_image',
    )
    readonly_fields = ('front_image_tag', 'side_image_tag', 'rear_image_tag',)
    search_fields = ['=user__username', '=user__pk']


@admin.register(MealFault)
class MealFaultAdmin(NoDeleteModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['code']
        else:
            return []

    list_display = ['id', 'title', 'code', 'comment', 'is_active', 'is_public', 'is_manual']


@admin.register(MealNoticeTemplateCategory)
class MealNoticeTemplateCategoryAdmin(NoDeleteModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['code']
        else:
            return []

    list_display = ['id', 'title', 'code', 'is_active', ]


@admin.register(MealNoticeTemplate)
class MealNoticeTemplateAdmin(NoDeleteModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['code']
        else:
            return []

    list_display = ['id', 'template', 'category', 'code', 'is_active', ]


def clear_type(modeladmin, request, queryset):
    queryset.filter(is_verified=False).update(
        component_type=None,
        verified_by=request.user,
        is_verified=True,
        verified_at=timezone.now()
    )


clear_type.short_description = "Очистить категорию"


def set_product_type(product_type, modeladmin, request, queryset):
    queryset.filter(is_verified=False).update(
        component_type=product_type,
        verified_by=request.user,
        is_verified=True,
        verified_at=timezone.now()
    )


def set_product_type_bread(modeladmin, request, queryset):
    return set_product_type('bread', modeladmin, request, queryset)


set_product_type_bread.short_description = "Установить категорию: Хлеб"


def set_product_type_fat(modeladmin, request, queryset):
    return set_product_type('fat', modeladmin, request, queryset)


set_product_type_fat.short_description = "Установить категорию: Жирный продукт"


def set_product_type_carb(modeladmin, request, queryset):
    return set_product_type('carb', modeladmin, request, queryset)


set_product_type_carb.short_description = "Установить категорию: Готовые углеводы"


def set_product_type_rawcarb(modeladmin, request, queryset):
    return set_product_type('rawcarb', modeladmin, request, queryset)


set_product_type_rawcarb.short_description = "Установить категорию: Сухие углеводы"


def set_product_type_fatcarb(modeladmin, request, queryset):
    return set_product_type('fatcarb', modeladmin, request, queryset)


set_product_type_fatcarb.short_description = "Установить категорию: Жирные углеводы"


def set_product_type_protein(modeladmin, request, queryset):
    return set_product_type('protein', modeladmin, request, queryset)


set_product_type_protein.short_description = "Установить категорию: Белковый продукт"


def set_product_type_deadweight(modeladmin, request, queryset):
    return set_product_type('deadweight', modeladmin, request, queryset)


set_product_type_deadweight.short_description = "Установить категорию: Балласт"


def set_product_type_veg(modeladmin, request, queryset):
    return set_product_type('veg', modeladmin, request, queryset)


set_product_type_veg.short_description = "Установить категорию: Овощи"


def set_product_type_carbveg(modeladmin, request, queryset):
    return set_product_type('carbveg', modeladmin, request, queryset)


set_product_type_carbveg.short_description = "Установить категорию: Запасающие овощи"


def set_product_type_fruit(modeladmin, request, queryset):
    return set_product_type('fruit', modeladmin, request, queryset)


set_product_type_fruit.short_description = "Установить категорию: Фрукты"


def set_product_type_dfruit(modeladmin, request, queryset):
    return set_product_type('dfruit', modeladmin, request, queryset)


set_product_type_dfruit.short_description = "Установить категорию: Сухофрукты"


def set_product_type_desert(modeladmin, request, queryset):
    return set_product_type('desert', modeladmin, request, queryset)


set_product_type_desert.short_description = "Установить категорию: Десерт"


def set_product_type_drink(modeladmin, request, queryset):
    return set_product_type('drink', modeladmin, request, queryset)


set_product_type_drink.short_description = "Установить категорию: Калорийный напиток"


def set_product_type_alco(modeladmin, request, queryset):
    return set_product_type('alco', modeladmin, request, queryset)


set_product_type_alco.short_description = "Установить категорию: Алкоголь"


def set_product_type_unknown(modeladmin, request, queryset):
    return set_product_type('unknown', modeladmin, request, queryset)


set_product_type_unknown.short_description = "Установить категорию: Продукт с неопределенным составом"


class MealProductTagInline(admin.TabularInline):
    verbose_name_plural = "Теги"
    model = MealProductTag.products.through
    extra = 1


class MealProductAliasInline(admin.TabularInline):
    verbose_name_plural = "Синонимы"
    model = MealProductAlias
    extra = 1


@admin.register(MealProductTag)
class MealProductTagAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['system_code']
        else:
            return []

    list_display = ['title', 'system_code', 'is_analytical']
    exclude = ['products']


class MealProductForm(forms.ModelForm):
    class Meta:
        model = MealProduct
        exclude = ['id', 'tags']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and MealProduct.objects.filter(title=title).exclude(pk=self.instance.pk).exists():
            # ограничение на (title, language)
            raise forms.ValidationError(
                "Продукт с таким наименование уже существует (ограничение {title, language=ru})."
            )

        return title


@admin.register(MealProduct)
class MealProductAdmin(NoDeleteModelAdmin):
    def get_queryset(self, request):
        qs = super(MealProductAdmin, self).get_queryset(request)
        return qs.prefetch_related('aliases')

    def save_model(self, request, obj, form, change):
        if not obj.verified_by_id and obj.is_verified:
            obj.verified_by = request.user

        super(MealProductAdmin, self).save_model(request, obj, form, change)

    def get_nutrition(self, obj):
        protein = '%.1f' % obj.protein_percent if obj.protein_percent is not None else '--'
        fat = '%.1f' % obj.fat_percent if obj.fat_percent is not None else '--'
        carb = '%.1f' % obj.carb_percent if obj.carb_percent is not None else '--'
        has_sugar = ', сахара' if obj.is_fast_carbs else ''
        return '%s/%s/%s%s' % (
            protein,
            fat,
            carb,
            has_sugar,
        )

    def get_aliases(self, obj):
        aliases = obj.aliases.all()
        return ", ".join([a.title for a in aliases])

    get_aliases.short_description = "Синонимы"

    inlines = (MealProductAliasInline, MealProductTagInline,)
    form = MealProductForm
    get_nutrition.short_description = 'БЖУ'

    list_per_page = 50
    list_display = ['title', 'get_aliases', 'component_type', 'get_nutrition', 'is_verified', ]
    readonly_fields = ['verified_at', 'verified_by', 'language']
    search_fields = ['title', 'aliases__title']
    list_filter = ['is_verified', 'component_type', 'tags']
    actions = [
        clear_type,
        set_product_type_bread,
        set_product_type_fat,
        set_product_type_carb,
        set_product_type_rawcarb,
        set_product_type_fatcarb,
        set_product_type_protein,
        set_product_type_deadweight,
        set_product_type_veg,
        set_product_type_carbveg,
        set_product_type_fruit,
        set_product_type_dfruit,
        set_product_type_desert,
        set_product_type_drink,
        set_product_type_alco,
        set_product_type_unknown,
    ]
