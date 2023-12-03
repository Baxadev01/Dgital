# -*- coding: utf-8 -*-

from django.contrib import admin
from support.models import Ticket
# from django.db import models
from django.contrib.admin.utils import flatten_fieldsets

from django.http.response import Http404


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


class TicketAdmin(NoDeleteModelAdmin):
    list_display = ['id', 'full_name', 'email', 'subject', 'assignee', 'posted_at', 'status']
    readonly_fields = ['full_name', 'email', 'posted_at', 'subject', 'body', 'signature', ]
    list_filter = ['status', 'assignee', ]


admin.site.register(Ticket, TicketAdmin)
