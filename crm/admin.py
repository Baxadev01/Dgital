# -*- coding: utf-8 -*-

import html
from builtins import str as text
from datetime import date, timedelta

from admin_auto_filters.filters import AutocompleteFilter

from django.db.models import Q, Exists, OuterRef
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http.request import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from import_export import resources
from import_export.admin import ExportActionModelAdmin
from markdownx.utils import markdownify

from crm.models import Campaign, Payment, DiscountCode, Application, AdmissionTestQuestion, UserAdmissionTest, \
    UserAdmissionTestQuestion, RenewalRequest, TelegramMailTemplate, TariffHistory
from srbc.admin import NoDeleteModelAdmin, UserFilter, WaveFilter,  \
    UserBasedCommunicationModeFilter, UserBasedWaveListFilter
from srbc.models import Tariff, TariffGroup, Wave


class DiscountCodeFilter(AutocompleteFilter):
    title = 'Скидки'
    field_name = 'discount_code'


class PaymentWaveFilter(AutocompleteFilter):
    title = 'Payment Wave'
    field_name = 'wave'


class CampaignFilter(AutocompleteFilter):
    title = 'Старт'
    field_name = 'campaign'


def approve_application(modeladmin, request, queryset):
    for application in queryset:
        messages = []
        try:
            admission_test = application.user.admission_test
            if admission_test.status != 'ACCEPTED':
                admission_test.status = 'ACCEPTED'
                admission_test.save()
                messages.append('test approved')
        except User.admission_test.RelatedObjectDoesNotExist:
            pass

        if application.tariff:
            application.user.profile.tariff_next = application.tariff
            application.user.profile.save(update_fields=['tariff_next'])
            messages.append('payment_allowed (%s) ' % application.tariff)

        if messages:
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(application).pk,
                object_id=application.id,
                object_repr=str(application),
                action_flag=CHANGE,
                change_message='Application approved: %s' % ', '.join(messages)
            )


def get_profile_ids(modeladmin, request, queryset):
    ids = queryset.values_list('user_id', flat=True)

    messages.success(
        request,
        "User IDs: %s" % ', '.join(['%s' % i for i in ids])
    )


approve_application.short_description = "Approve application/allow payment"
get_profile_ids.short_description = "Get Profile IDs"


def deny_payment(modeladmin, request, queryset):
    for application in queryset:
        application.user.profile.tariff_next = None

        application.user.profile.save(update_fields=['tariff_next', ])

        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(application.user.profile).pk,
            object_id=application.user.profile.id,
            object_repr=text(application.user.profile),
            action_flag=CHANGE,
            change_message='Payment canceled'
        )


deny_payment.short_description = "Disallow payments"


def cancel_payment(modeladmin, request, queryset):
    for payment in queryset:
        application = payment.user.application
        payment.status = 'CANCELED'

        application.user.profile.tariff_next = None
        application.user.profile.save(update_fields=['tariff_next', ])
        payment.save(update_fields=['status', ])

        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(payment).pk,
            object_id=payment.id,
            object_repr=str(payment),
            action_flag=CHANGE,
            change_message='Payment canceled'
        )

        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(application).pk,
            object_id=application.id,
            object_repr=text(application),
            action_flag=CHANGE,
            change_message='Payment canceled'
        )

        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(application.user.profile).pk,
            object_id=application.user.profile.id,
            object_repr=text(application.user.profile),
            action_flag=CHANGE,
            change_message='Payment canceled'
        )


cancel_payment.short_description = "Cancel and deny payment"


class RenewalListFilter(SimpleListFilter):
    title = _('Продление')

    parameter_name = 'renewal_request'

    def lookups(self, request, model_admin):
        return [
            ('do', _('продолжаю')),
            ('donot', _('НЕпродолжаю')),
            ('ignore', _('игнорирую')),
        ]

    def queryset(self, request, queryset):

        last_wave = Wave.objects.filter(start_date__lte=date.today()).order_by('-start_date').first()
        last_start_date = last_wave.start_date

        if self.value() == 'do':
            renewal_qs = RenewalRequest.objects.filter(
                date_added__date__gte=last_start_date,
                request_type='POSITIVE'
            ).values_list('user_id', flat=True)
            return queryset.filter(user_id__in=renewal_qs)
        elif self.value() == 'donot':
            renewal_qs = RenewalRequest.objects.filter(
                date_added__date__gte=last_start_date,
                request_type='NEGATIVE'
            ).values_list('user_id', flat=True)
            return queryset.filter(user_id__in=renewal_qs)
        elif self.value() == 'ignore':
            renewal_qs = RenewalRequest.objects.filter(
                date_added__date__gte=last_start_date
            ).values_list('user_id', flat=True)
            return queryset.exclude(user_id__in=renewal_qs)
        else:
            return queryset


class ProfileWaveListFilter(SimpleListFilter):
    title = _('Статус пользотвателя')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'profile_wave'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ('empty', _('Абитуриент')),
            ('notempty', _('Участник')),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        today = date.today()

        if self.value():
            is_wave_null = self.value() == 'empty'

            queryset = queryset.filter(
                user__profile__active_tariff_history__wave__isnull=is_wave_null
            )

        return queryset


class ProfileExpirationListFilter(SimpleListFilter):
    title = _('Оплачено до')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'profile_expire'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ('soon', _('Ближайший старт')),
            ('4w', _('Следующий старт')),
            ('8w', _('Продлён')),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        today = date.today()
        if self.value() == 'soon':
            return queryset.filter(
                user__profile__active_tariff_history__valid_until__lte=today + timedelta(weeks=4)
            )
        elif self.value() == '4w':
            return queryset.filter(
                user__profile__active_tariff_history__valid_until__lte=today + timedelta(weeks=8),
                user__profile__active_tariff_history__valid_until__gt=today + timedelta(weeks=4)
            )
        elif self.value() == '8w':
            return queryset.filter(
                user__profile__active_tariff_history__isnull=False,
                # кажется, что такого условия вполне должно хватить для нормального хода работы, 
                # но возможно есть какие-то записи у сержантов, которые не попадут.. важно нет ?

                # возможно просто оставить next и все ? без даты ? все равно на 8 недель же ?
                user__profile__next_tariff_history__valid_until__gt=today + timedelta(weeks=8)
            )
        else:
            return queryset


@admin.register(Campaign)
class CampaignAdmin(NoDeleteModelAdmin):
    # list_filter = ['user', 'author', 'label', 'is_published', 'date_added']
    list_display = ['id', 'title', 'start_date', 'is_active', 'admission_status', ]
    search_fields = ['title', ]
    readonly_fields = ['is_admission_open', 'admission_start_date', 'admission_end_date', 'admission_status']
    raw_id_fields = ['wave_chat', 'wave_channel', ]


@admin.register(RenewalRequest)
class RenewalRequestAdmin(NoDeleteModelAdmin):
    def profile_url(self, obj):
        return format_html(
            "&nbsp;<a href='/admin/srbc/profile/{profile_id}/change/'>Профиль</a><br />"
            "&nbsp;<a href='/profile/!{user_id}/'>ЛК</a><br />"
            "&nbsp;<a href='/admin/auth/user/{user_id}/change/'>Юзер*</a>",
            profile_id=obj.user.profile.pk,
            user_id=obj.user.pk
        )

    def wave_title(self, obj):
        return obj.user.profile.wave.title if obj.user.profile.wave else ''

    profile_url.short_description = "Profile"
    wave_title.short_description = "Wave"

    list_display = ['id', 'user', 'wave_title', 'request_type', 'comment', 'status', 'profile_url']
    list_filter = ['request_type', 'status']
    search_fields = ['=user__id', 'user__username']
    fields = ['user', 'request_type', 'comment', 'date_added', 'status', 'comment_internal', 'payment_special', ]
    readonly_fields = ['request_type', 'comment', 'user', 'date_added']


@admin.register(TelegramMailTemplate)
class TelegramMailTemplateAdmin(NoDeleteModelAdmin):
    list_display = ['id', 'title', 'slug']
    readonly_fields = ['slug']


@admin.register(TariffHistory)
class TariffHistoryAdmin(admin.ModelAdmin):
    def profile_url(self, obj):
        return format_html(
            "<a href='/admin/srbc/profile/{id}/change/'>"
            "<i class='glyphicon icon-{icon}-sign'></i>&nbsp;Профиль"
            "</a>",
            id=obj.user.profile.pk,
            icon='ok' if obj.user.profile.is_active else 'remove'
        )

    profile_url.short_description = "Profile"

    def user_url(self, obj):
        return format_html(
            "<a href='/admin/auth/user/{id}/change/'>"
            "<i class='glyphicon icon-{icon}-sign'></i>&nbsp;{user}"
            "</a>",
            id=obj.user.pk,
            icon='ok' if obj.user.profile.is_active else 'remove',
            user=obj.user.username
        )

    user_url.short_description = "User"

    def payment_url(self, obj):
        if obj.payment:
            return format_html(
                "<a href='/admin/crm/payment/{id}/change/'><i class='glyphicon icon-user'></i>&nbsp;{id}</a>",
                id=obj.payment.pk,
            )

        return None

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user', 'valid_from', 'valid_until', 'tariff')
        else:
            return self.readonly_fields

    # из автокомплита убран tariff - иначе код ниже не имеет смысла, он все равно фильтрует по всем
    # если он там будет критичен - то либо через form пытаться, либо еще пробовать разные варианты, мб get_search_results
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tariff":
            kwargs["queryset"] = Tariff.objects.filter(is_archived=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    payment_url.short_description = "Payment"

    list_display = ['id', 'user_url', 'wave', 'valid_from', 'valid_until',
                    'is_active', 'payment_url', 'profile_url', 'tariff']
    raw_id_fields = ['user', 'payment', ]
    autocomplete_fields = ['wave',  ]

    list_filter = [UserFilter, WaveFilter, 'created_at']

    class Media:
        pass


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        if obj is None:
            
            if request.user.has_perm('crm.add_advanced_payment'):
                return self.add_advanced_fields
            else:
                return self.add_fields

        return self.fields
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return ()
    
    add_advanced_fields = [
        'user',
        'payment_provider',
        'payment_id',
        'status',
        'date_added',
        'amount',
        'currency',
        'tariff',
        'discount_code',
        'payment_type',
        'payment_url',
        'wave',
        'paid_at',
    ]

    list_display = [
        'id', 'user', 'discount_code', 'amount', 'currency', 'payment_id', 'payment_provider',
        'status', 'date_added',
    ]

    search_fields = ['=id', '=payment_id', '=user__id', '=user__username', ]
    raw_id_fields = ['user']
    add_fields = ['user', 'discount_code']

    fields = [
        'user',
        'payment_provider',
        'payment_id',
        'status',
        'date_added',
        'amount',
        'currency',
        'tariff',
        'discount_code',
        'payment_type',
        'payment_url',
        'wave',
        'paid_at',
        'last_updated_at',
    ]

    readonly_fields = [
        'paid_at',
        'last_updated_at',
        'tariff',
    ]

    actions = [cancel_payment]

    list_filter = [
        'currency', 'payment_provider', 'status', 'date_added',
        DiscountCodeFilter,
        UserBasedWaveListFilter,
        'wave'
    ]
    # suit_list_filter_horizontal = ['user__profile__wave', 'wave']

    def has_add_permission(self, request: HttpRequest) -> bool:
        if request.user.has_perm('crm.add_advanced_payment'):
            return True
        return super().has_add_permission(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tariff":
            kwargs["queryset"] = Tariff.objects.filter(is_archived=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    class Media:
        pass


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'is_applied', 'applied_by', 'dicount_percent', 'payment_type', ]
    search_fields = ['code']


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'fee_rub', 'fee_eur', 'tariff_next', 'tariff_group', ]
    search_fields = ['=id', 'title']


@admin.register(TariffGroup)
class TariffGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'communication_mode', ]


# class ApplicationEmailExport(resources.ModelResource):
#     class Meta:
#         model = Application
#         fields = (
#             'user__id',
#             'user__first_name', 'user__last_name',
#             'user__username',
#             'user__profile__wave__title',
#             'user__profile__is_active',
#             # TODO как вернется в строй переписать
#             # 'user__profile__communication_mode',
#             'user__email',
#             'user__application__country', 'user__application__city',
#         )


@admin.register(Application)
class ApplicationAdmin(ExportActionModelAdmin):
    # def get_readonly_fields(self, request, obj=None):
    #     if request.user.is_superuser:
    #         return self.readonly_fields
    #
    #     return list(set(
    #         [field.name for field in self.opts.local_fields] +
    #         [field.name for field in self.opts.local_many_to_many]
    #     ))

    def get_queryset(self, request):
        return Application.objects.select_related('user', 'user__profile', 'campaign')

    def lookup_allowed(self, lookup, value):
        return True

    def profile_url(self, obj):
        return format_html(
            "<a href='/admin/srbc/profile/{id}/change/'><i class='glyphicon icon-user'></i>&nbsp;{username}</a>",
            id=obj.user.profile.pk,
            username=obj.user.username
        )

    profile_url.short_description = "Profile"

    # def facebook_url(self, obj):
    #     return format_html(
    #         "<a href='/profile/{id}/facebook/' target='_blank'>link</a>",
    #         id=obj.user.pk
    #     )
    #
    # facebook_url.short_description = "Facebook"

    def user_link(self, obj):
        return format_html(
            "{username} (#{user_id})&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/auth/user/{user_id}/change/'>Аккаунт</a>&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/srbc/profile/{profile_id}/change/'>Профиль</a>",
            username=obj.user.username,
            user_id=obj.user.pk,
            profile_id=obj.user.profile.pk,
        )

    user_link.short_description = "Аккаунт участника"

    def active_payment_order_link(self, obj):
        if obj.active_payment_order:
            return format_html(
                "<a href='/admin/crm/payment/{order_id}/change/'>Счёт #{order_id} ({order_status})</a>",
                order_id=obj.active_payment_order.pk,
                order_status=obj.active_payment_order.status,
            )
        else:
            return '-'

    def userid(self, obj):
        return obj.user_id
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tariff":
            kwargs["queryset"] = Tariff.objects.filter(is_archived=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    userid.short_description = 'ID'
    userid.admin_order_field = 'user_id'

    list_display = [
        'userid', 'user', 'first_name', 'last_name', 'campaign', 'country',
        # 'email_status',
        'admission_status',
        # 'social_acc_status', 'is_approved',
        'is_payment_allowed', 'profile_url',
        # 'facebook_url',
        'is_payment_special',
    ]
    search_fields = ['=user__id', '=user__username', ]
    raw_id_fields = ['user']

    actions = [
        approve_application,
        deny_payment,
        get_profile_ids,
    ]

    fields = (
        'campaign', 'is_approved', 'social_acc_status',
        'user_link',
        # 'facebook_url',
        'is_payment_allowed',
        'is_payment_special',
        'active_payment_order_link',
        'admission_status',
        'gender', 'first_name', 'last_name', 'phone',
        'country', 'city',
        'height', 'weight', 'goal_weight', 'goals', 'age', 'birth_year', 'sickness',
        'baby_case', 'baby_birthdate',
        'tos_signed_date', 'tariff'
    )

    readonly_fields = [
        'user_link',
        # 'facebook_url',
        'gender', 'first_name', 'last_name', 'phone',
        'country', 'city',
        'age', 'sickness', 'goals',
        'admission_status',
        'tos_signed_date',
        'active_payment_order_link',
    ]

    list_filter = [
        CampaignFilter,
        UserBasedWaveListFilter,
        'tariff__tariff_group__communication_mode',
        'admission_status', 'is_payment_allowed', 'is_payment_special',
        ProfileExpirationListFilter, RenewalListFilter,
    ]
    # suit_list_filter_horizontal = ['user__profile__wave', ]

    # resource_class = ApplicationEmailExport

    class Media:
        pass


@admin.register(AdmissionTestQuestion)
class AdmissionTestQuestionAdmin(NoDeleteModelAdmin):
    def text_md(self, obj):
        return mark_safe(markdownify(obj.text))

    text_md.short_description = "Text"

    list_display = ['text_md', 'is_active', ]


class AdmissionResultEmailExport(resources.ModelResource):
    class Meta:
        model = UserAdmissionTest
        fields = (
            'user__id',
            'user__first_name', 'user__last_name',
            'user__email',
            'user__application__country', 'user__application__city',
        )


@admin.register(UserAdmissionTest)
class UserAdmissionTestAdmin(ExportActionModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['user']
        else:
            return self.readonly_fields

    def questions_answers(self, obj):
        test_questions_objects = UserAdmissionTestQuestion.objects.filter(admission_test__pk=obj.id).order_by(
            'question_num').all()
        questions_text = ''
        for question in test_questions_objects:
            ans = '<i>Рацион</i>:<div>%s</div>' % markdownify(question.text)
            ans += '<i>Правильные ответы:</i>'
            ans += '<ul style="color: #339933">'
            if question.source_question.answer_ok:
                ans += "<li><strong>Соответствует методичке</strong></li>"
            if question.source_question.answer_sweet:
                ans += "<li><strong>Сладкое натощак</strong></li>"
            if question.source_question.answer_interval:
                ans += "<li><strong>Нарушены интервалы</strong></li>"
            if question.source_question.answer_protein:
                ans += "<li><strong>Недостаток белка</strong></li>"
            if question.source_question.answer_carb:
                ans += "<li><strong>Неверное количество углеводов</strong></li>"
            if question.source_question.answer_fat:
                ans += "<li><strong>Превышение жирности</strong></li>"
            if question.source_question.answer_weight:
                ans += "<li><strong>Неверные навески</strong></li>"
            ans += '</ul>'
            ans += '<i>Ответы участника:</i>'
            ans += '<ul style="color: #333399">'
            if question.answer_ok:
                ans += "<li><strong>Соответствует методичке</strong>: %s</li>" % html.escape(question.answer_ok_comment)
            if question.answer_sweet:
                ans += "<li><strong>Сладкое натощак</strong>: %s</li>" % html.escape(question.answer_sweet_comment)
            if question.answer_interval:
                ans += "<li><strong>Нарушены интервалы</strong>: %s</li>" % html.escape(
                    question.answer_interval_comment)
            if question.answer_protein:
                ans += "<li><strong>Недостаток белка</strong>: %s</li>" % html.escape(question.answer_protein_comment)
            if question.answer_carb:
                ans += "<li><strong>Неверное количество углеводов</strong>: %s</li>" % html.escape(
                    question.answer_carb_comment)
            if question.answer_fat:
                ans += "<li><strong>Превышение жирности</strong>: %s</li>" % html.escape(question.answer_fat_comment)
            if question.answer_weight:
                ans += "<li><strong>Неверные навески</strong>: %s</li>" % html.escape(question.answer_weight_comment)
            ans += '</ul><hr />'
            questions_text += ans

        return format_html(questions_text)

    questions_answers.short_description = "Ответы на вопросы теста"

    def questions_url(self, obj):
        return format_html(
            "<a href='/admin/crm/useradmissiontestquestion/?admission_test__exact={id}' target='_blank'>"
            "Вопросы теста</a>",
            id=obj.pk
        )

    questions_url.short_description = "Questions"

    def user_link(self, obj):
        return format_html(
            "{username} (#{user_id})&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/auth/user/{user_id}/change/'>Аккаунт</a>&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/srbc/profile/{profile_id}/change/'>Профиль</a>&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/crm/application/{application_id}/change/'>Анкета</a>",
            username=obj.user.username,
            user_id=obj.user.pk,
            profile_id=obj.user.profile.pk,
            application_id=obj.user.application.pk
        )
    
    def tariff(self, obj):
        tariff = obj.user.application.tariff

        return format_html(
            "<a href='/admin/srbc/tariff/{tariff_id}/change/'>{tariff_title}</a>&nbsp;&nbsp;&nbsp;",
            tariff_id=tariff.id,
            tariff_title=tariff.title

        )

    user_link.short_description = "Аккаунт участника"

    resource_class = AdmissionResultEmailExport

    list_display = ['id', 'user', 'status', 'question_asked', 'questions_url', 'completed_date', 'reviewed_date', ]
    raw_id_fields = ['user']
    search_fields = ['=user__pk', '=user__username', ]
    list_filter = [
        'status',
        ProfileWaveListFilter,
    ]

    readonly_fields = ['user_link', 'started_date', 'tariff', 'questions_answers', 'question_asked', 'recommendation_info',
                       'completed_date',
                       'reviewed_date', ]


@admin.register(UserAdmissionTestQuestion)
class UserAdmissionTestQuestionAdmin(admin.ModelAdmin):
    def combined_answer(self, obj):
        ans = '<ul>'
        if obj.answer_ok:
            ans += "<li><strong>Соответствует методичке</strong>: %s</li>" % html.escape(obj.answer_ok_comment)
        if obj.answer_sweet:
            ans += "<li><strong>Сладкое натощак</strong>: %s</li>" % html.escape(obj.answer_sweet_comment)
        if obj.answer_interval:
            ans += "<li><strong>Нарушены интервалы</strong>: %s</li>" % html.escape(obj.answer_interval_comment)
        if obj.answer_protein:
            ans += "<li><strong>Недостаток белка</strong>: %s</li>" % html.escape(obj.answer_protein_comment)
        if obj.answer_carb:
            ans += "<li><strong>Неверное количество углеводов</strong>: %s</li>" % html.escape(obj.answer_carb_comment)
        if obj.answer_fat:
            ans += "<li><strong>Превышение жирности</strong>: %s</li>" % html.escape(obj.answer_fat_comment)
        if obj.answer_weight:
            ans += "<li><strong>Неверные навески</strong>: %s</li>" % html.escape(obj.answer_weight_comment)
        ans += '</ul>'
        return mark_safe(ans)

    combined_answer.short_description = "Answer"

    def combined_correct_answer(self, obj):
        ans = '<ul>'
        if obj.source_question.answer_ok:
            ans += "<li><strong>Соответствует методичке</strong></li>"
        if obj.source_question.answer_sweet:
            ans += "<li><strong>Сладкое натощак</strong></li>"
        if obj.source_question.answer_interval:
            ans += "<li><strong>Нарушены интервалы</strong></li>"
        if obj.source_question.answer_protein:
            ans += "<li><strong>Недостаток белка</strong></li>"
        if obj.source_question.answer_carb:
            ans += "<li><strong>Неверное количество углеводов</strong></li>"
        if obj.source_question.answer_fat:
            ans += "<li><strong>Превышение жирности</strong></li>"
        if obj.source_question.answer_weight:
            ans += "<li><strong>Неверные навески</strong></li>"
        ans += '</ul>'
        return mark_safe(ans)

    combined_correct_answer.short_description = "Correct Answer"

    def text_md(self, obj):
        return mark_safe(markdownify(obj.text))

    text_md.short_description = "Text"
    list_display = ['id', 'text_md', 'question_num', 'is_answered', 'combined_answer', 'combined_correct_answer', ]
    search_fields = ['=admission_test__user__pk', ]
    readonly_fields = [
        'answer_ok', 'answer_ok_comment',
        'answer_sweet', 'answer_sweet_comment',
        'answer_interval', 'answer_interval_comment',
        'answer_protein', 'answer_protein_comment',
        'answer_carb', 'answer_carb_comment',
        'answer_fat', 'answer_fat_comment',
        'answer_weight', 'answer_weight_comment',
    ]
