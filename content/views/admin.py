# -*- coding: utf-8 -*-
from datetime import date
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

from content.forms import TGSendmailForm, TGSendmailFormSpam
from content.models import TGNotification
from content.models import TGNotificationTemplate
from crm.models import Application
from srbc.decorators import is_channel_admin, is_superuser
from srbc.models import User, Profile


@login_required
@user_passes_test(is_channel_admin)
def channel_admin(request):
    default_message_type = 'QUESTION'

    user_groups = request.user.groups.values_list('name', flat=True)

    if 'ChannelAdminFeedback' in user_groups:
        default_message_type = 'FEEDBACK'
    if 'ChannelAdminMeal' in user_groups:
        default_message_type = 'MEAL'
    if 'ChannelAdminFormula' in user_groups:
        default_message_type = 'FORMULA'

    return render(
        request,
        'content/channel_admin.html',
        {
            'default_message_type': default_message_type,
        }
    )


@login_required
@user_passes_test(is_superuser)
def sendmail_admin(request):
    notifications_count = 0
    notifications_count_result = None

    if request.POST.get('action'):
        if request.GET.get('spam'):
            form = TGSendmailFormSpam(request.POST)
        else:
            form = TGSendmailForm(request.POST)

        if form.is_valid():
            users_to_send = []
            exclude_receievers = []
            if form.cleaned_data['exclude_fingerprint']:
                exclude_receievers = TGNotification.objects.filter(
                    fingerprint=form.cleaned_data['exclude_fingerprint']
                ).values_list('user', flat=True).all()

            if form.cleaned_data['list_mode'] == 'SPAM':
                users_to_send = Profile.objects.filter(
                    telegram_id__isnull=False
                ).values_list('user', flat=True).all()

            if form.cleaned_data['list_mode'] == 'CAMPAIGN':
                users_to_send = Application.objects.filter(
                    campaign=form.cleaned_data['campaign']
                ).exclude(
                    user_id__in=exclude_receievers
                ).values_list('user', flat=True).all()

            if form.cleaned_data['list_mode'] == 'IDS':
                ids_list = form.cleaned_data['user_ids'].split(',')
                user_ids = [i.strip() for i in ids_list if len(i.strip())]

                users_to_send = User.objects.filter(
                    id__in=user_ids
                ).exclude(
                    id__in=exclude_receievers
                ).values_list('id', flat=True).all()

            if form.cleaned_data['list_mode'] == 'CAMPAIGNCHANNEL':
                today = date.today()
                users_to_send = Application.objects.filter(
                    campaign=form.cleaned_data['campaign'],
                    # считаем активным тариф, у которого дата окончания больше или равно сегодняшнему дню
                    user__tariff_history__valid_until__gte=today,
                    user__tariff_history__is_active=True,
                    user__tariff_history__tariff__tariff_group__communication_mode='CHANNEL'
                ).exclude(
                    user_id__in=exclude_receievers
                ).values_list('user', flat=True).all()

            if form.cleaned_data['list_mode'] == 'WAVE':
                users_to_send = Profile.objects.filter(
                    wave=form.cleaned_data['wave'],
                ).exclude(
                    user_id__in=exclude_receievers
                ).values_list('user', flat=True).all()

            if form.cleaned_data['list_mode'] == 'FINGERPRINT':
                users_to_send = TGNotification.objects.filter(
                    fingerprint=form.cleaned_data['source_fingerprint'],
                ).exclude(
                    user_id__in=exclude_receievers
                ).values_list('user', flat=True).all()

            if users_to_send:
                for u in users_to_send:
                    TGNotification(
                        user_id=u,
                        content=form.cleaned_data['content'],
                        fingerprint=form.cleaned_data['fingerprint'],
                        status='PENDING'
                    ).save()
                    notifications_count += 1

            return redirect('/staff/sendmail/?sent=%s' % notifications_count)

    else:
        if request.GET.get('spam'):
            if request.POST:
                form = TGSendmailFormSpam(request.POST)
            else:
                form = TGSendmailFormSpam()
        else:
            if request.POST:
                form = TGSendmailForm(request.POST)
            else:
                form = TGSendmailForm()

        notifications_count_result = request.GET.get('sent')

    templates = TGNotificationTemplate.objects.filter(is_visible=True)

    return render(request, 'content/tg_sendmail.html', {
        "form": form,
        "templates": templates,
        "notifications_count": notifications_count_result,
    })
