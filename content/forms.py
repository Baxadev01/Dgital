# -*- coding: utf-8 -*-
import datetime

from django import forms

from content.models.utils import generate_uuid
from crm.models import Campaign
from srbc.models import Wave


class TGSendmailForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea)
    list_mode = forms.ChoiceField(
        label="Получатели рассылки",
        choices=(
            ('CAMPAIGN', "По дате старта"),
            ('CAMPAIGNCHANNEL', "По дате старта, заочники "),
            ('WAVE', "Поток"),
            ('FINGERPRINT', "Получатели существующей рассылки"),
            ('IDS', "По ID пользователей"),
        )
    )

    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.filter(
            start_date__lte=datetime.date.today() + datetime.timedelta(days=31)
        ).order_by('-start_date').all(),
        label="Кампания",
        required=False
    )

    wave = forms.ModelChoiceField(
        queryset=Wave.objects.order_by('-start_date').all(),
        label="Поток",
        required=False
    )
    user_ids = forms.CharField(max_length=2048, label="ID пользователей", required=False)
    fingerprint = forms.CharField(max_length=64, label="Метка рассылки", initial=generate_uuid)
    exclude_fingerprint = forms.CharField(
        max_length=64, label="Исключить получателей рассылки",
        required=False
    )
    source_fingerprint = forms.CharField(
        max_length=64, label="Предыдущая рассылка",
        required=False
    )


class TGSendmailFormSpam(forms.Form):
    content = forms.CharField(widget=forms.Textarea)
    list_mode = forms.ChoiceField(
        label="Получатели рассылки",
        choices=(
            ('SPAM', "Все вааааще"),
        ),
    )

    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.filter(
            start_date__lte=datetime.date.today() + datetime.timedelta(days=31)
        ).order_by('-start_date').all(),
        label="Кампания",
        required=False
    )

    wave = forms.ModelChoiceField(
        queryset=Wave.objects.order_by('-start_date').all(),
        label="Поток",
        required=False
    )
    user_ids = forms.CharField(max_length=2048, label="ID пользователей", required=False)
    fingerprint = forms.CharField(max_length=64, label="Метка рассылки", required=True)
    exclude_fingerprint = forms.CharField(
        max_length=64, label="Исключить получателей рассылки",
        required=False
    )
    source_fingerprint = forms.CharField(
        max_length=64, label="Предыдущая рассылка",
        required=False
    )
