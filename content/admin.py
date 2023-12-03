# -*- coding: utf-8 -*-

from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from markdownx.admin import MarkdownxModelAdmin
from markdownx.utils import markdownify

from content.models import Recipe, Basics, Meeting, TGMessage, TGPost, Picture, Article, TGChat, TGChatParticipant, \
    Dialogue, ChatQuestion, AnalysisTemplate, \
    TGNotificationTemplate, TGNotification, TGTranslation
from srbc.admin import NoDeleteModelAdmin


class UserFilter(AutocompleteFilter):
    title = 'Пользователи'
    field_name = 'user'


class AuthorFilter(AutocompleteFilter):
    title = 'Авторы'
    field_name = 'author'


class ChannelFilter(AutocompleteFilter):
    title = 'Каналы'
    field_name = 'channel'


class ChatFilter(AutocompleteFilter):
    title = 'Чаты'
    field_name = 'chat'


def ban_chat_members(modeladmin, request, queryset):
    items = queryset.all()
    for item in items:
        item.status = 'BANNED'
        item.save()


ban_chat_members.short_description = 'Ban chat members'


def unban_chat_members(modeladmin, request, queryset):
    items = queryset.all()
    for item in items:
        item.status = 'ALLOWED'
        item.save()


unban_chat_members.short_description = 'Unban chat members'


def restrict_chat_members(modeladmin, request, queryset):
    items = queryset.all()
    for item in items:
        item.status = 'RESTRICTED'
        item.save()


restrict_chat_members.short_description = 'Restrict chat members'


def unrestrict_chat_members(modeladmin, request, queryset):
    items = queryset.all()
    for item in items:
        item.status = 'UNRESTRICTED'
        item.save()


unrestrict_chat_members.short_description = 'Unrestrict chat members'


# FIXME НЕ ИСПОЛЬЗУЕТСЯ, есть такой же переписанный фильтр в crm,
# при необходимости заменить как в нем или использовать его

# class ProfileWaveListFilter(SimpleListFilter):
#     title = _('Статус пользотвателя')

#     # Parameter for the filter that will be used in the URL query.
#     parameter_name = 'profile_wave'

#     def lookups(self, request, model_admin):
#         """
#         Returns a list of tuples. The first element in each
#         tuple is the coded value for the option that will
#         appear in the URL query. The second element is the
#         human-readable name for the option that will appear
#         in the right sidebar.
#         """
#         return [
#             ('empty', _('Абитуриент')),
#             ('notempty', _('Участник')),
#         ]

#     def queryset(self, request, queryset):
#         """
#         Returns the filtered queryset based on the value
#         provided in the query string and retrievable via
#         `self.value()`.
#         """

#         if self.value() == 'empty':
#             return queryset.filter(user__profile__wave__isnull=True)
#         elif self.value() == 'notempty':
#             return queryset.filter(user__profile__wave__isnull=False)
#         else:
#             return queryset


class RecipeAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', ]
    search_fields = ['=id', 'title']


class BasicsAdmin(admin.ModelAdmin):
    list_display = ['id', 'keyword', 'type']
    search_fields = ['=id', 'keyword']
    list_filter = ['type', ]


class MeetingAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'delay_days', 'date', 'is_playable', 'status']
    search_fields = ['=id', 'title', 'description']
    list_filter = ['type', 'is_playable', 'status']


@admin.register(TGMessage)
class TGMessageAdmin(NoDeleteModelAdmin):
    def get_author_user(self, obj):
        label = '@%s' % obj.author.username

        return mark_safe(
            """<a href="/admin/srbc/profile/%s/change/">%s</a>""" % (
                obj.author.profile.pk,
                label,
            )
        )

    get_author_user.short_description = 'Author'
    get_author_user.admin_order_field = 'author__id'

    def author_link(self, obj):
        return format_html(
            "@{username} (#{user_id})&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/auth/user/{user_id}/change/'>Аккаунт</a>&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/srbc/profile/{profile_id}/change/'>Профиль</a>",
            username=obj.author.username,
            user_id=obj.author.pk,
            profile_id=obj.author.profile.pk
        )

    def get_answer_text(self, obj):
        return mark_safe(
            """<a href="/admin/content/tgpost/%s/change/">Ответ:</a><br />%s""" % (
                obj.answer.pk,
                markdownify(obj.answer.text),
            )
        )

    get_answer_text.short_description = 'Answer'

    list_display = ['id', 'get_author_user', 'status', 'created_at', 'resolved_at', 'message_type', ]
    search_fields = ['=id', ]
    readonly_fields = [
        'text', 'author_link', 'created_at', 'status',
        'resolved_at', 'resolved_by', 'get_answer_text', 'message_type',
    ]

    exclude = ['tg_message_id', 'answer', 'author', 'assigned', ]

    list_filter = ['assigned', 'status', 'message_type', 'author__profile__gender']


class TGPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'created_at', 'is_private', 'is_posted', 'channel', 'text']
    search_fields = ['=id', ]
    list_filter = ['is_private', 'is_posted', ChannelFilter, AuthorFilter]

    class Media:
        pass


class PictureAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'image', ]
    search_fields = ['=id', 'uid', 'title', ]
    exclude = ['uid', ]


class ArticleAdmin(MarkdownxModelAdmin):
    list_display = ['id', 'title', 'slug', 'is_published', 'is_public', 'sort_num', ]
    search_fields = ['=id', 'title', 'slug', 'text', ]
    list_filter = ['is_published', 'is_public', ]


@admin.register(TGChat)
class TGChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'title', 'chat_type', 'start_date', 'end_date', 'is_active']
    search_fields = ['=id', 'code', ]
    list_filter = ['start_date', 'end_date', 'chat_type', 'is_active']
    raw_id_fields = ['next_chat', ]


@admin.register(TGChatParticipant)
class TGChatMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'user_id', 'chat', 'status', 'status_changed', ]
    raw_id_fields = ['user']
    search_fields = ['=user__pk', 'user__username']
    list_filter = [ChatFilter, 'status', ]
    actions = [ban_chat_members, unban_chat_members, restrict_chat_members, unrestrict_chat_members]

    class Media:
        pass


@admin.register(AnalysisTemplate)
class AnalysisTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'text', 'is_visible', 'order_num', ]
    list_filter = ['is_visible']
    search_fields = ['=pk', 'title', 'text']


@admin.register(Dialogue)
class TGDialogueAdmin(NoDeleteModelAdmin):
    def username(self, obj):
        return obj.user.username if obj.user else '*GUEST*'

    username.short_description = "Profile"

    list_display = ['username', 'tg_user_id', 'created_at', 'text', 'is_incoming', 'answered_by', ]
    search_fields = ['=tg_user_id', '=user__id', '=user__username', 'text']
    list_filter = [UserFilter, 'created_at', 'answered_by', ]
    readonly_fields = ['user', 'tg_user_id', 'created_at', 'text', 'is_incoming', 'answered_by', 'tg_message_id', ]

    class Media:
        pass


@admin.register(ChatQuestion)
class ChatQuestionAdmin(NoDeleteModelAdmin):
    def get_author_user(self, obj):
        label = '@%s' % obj.author.username

        return mark_safe(
            """<a href="/admin/srbc/profile/%s/change/">%s</a>""" % (
                obj.author.profile.pk,
                label,
            )
        )

    get_author_user.short_description = 'Author'
    get_author_user.admin_order_field = 'author__id'

    def author_link(self, obj):
        return format_html(
            "@{username} (#{user_id})&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/auth/user/{user_id}/change/'>Аккаунт</a>&nbsp;&nbsp;&nbsp;"
            "<a href='/admin/srbc/profile/{profile_id}/change/'>Профиль</a>",
            username=obj.author.username,
            user_id=obj.author.pk,
            profile_id=obj.author.profile.pk
        )

    list_display = [
        'shortcut', 'get_author_user', 'chat', 'question_time', 'category', 'question_text', 'is_answered',
    ]

    list_filter = [
        'chat', 'category', 'is_answered', 'answered_by',
    ]

    search_fields = ['=author__pk', 'author__username', '=shortcut']

    exclude = ['author']

    readonly_fields = [
        'message_id', 'shortcut', 'author_link', 'chat', 'question_time', 'created_time', 'question_text',
        'answer_text', 'answered_time', 'answered_by',
    ]


@admin.register(TGNotificationTemplate)
class TGNotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'text', 'is_visible', 'system_code', ]
    list_filter = ['is_visible']
    search_fields = ['=pk', 'title', 'text']


@admin.register(TGNotification)
class TGNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'fingerprint', 'status', 'created_at', 'sent_at', 'error_message']
    readonly_fields = ['user', 'fingerprint', 'sent_at', 'sent_message', 'content', 'last_attempt_at']
    raw_id_fields = ['user', 'sent_message']
    list_filter = ['status']
    search_fields = ['=fingerprint', '=user__id']


@admin.register(TGTranslation)
class TGTranslationAdmin(NoDeleteModelAdmin):
    list_display = ['key', 'translation', 'description']
    search_fields = ['key', 'translation']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('key', )
        else:
            return self.readonly_fields


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Basics, BasicsAdmin)
admin.site.register(Meeting, MeetingAdmin)

admin.site.register(TGPost, TGPostAdmin)

admin.site.register(Picture, PictureAdmin)
admin.site.register(Article, ArticleAdmin)
