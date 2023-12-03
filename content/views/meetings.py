# -*- coding: utf-8 -*-
import os
from content.models import Meeting, MeetingPlayHistory
from datetime import date, datetime, timedelta

from django.shortcuts import get_object_or_404
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.http.response import Http404
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect, render
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from srbc.decorators import validate_user, has_desktop_access
from srbc.models import TariffGroup
from urllib.parse import urlparse

from content.utils import get_user_meetings


@login_required
@has_desktop_access
@validate_user
def meetings_list(request):
    if request.user.profile.tariff.tariff_group.meetings_access == TariffGroup.MEETINGS_NO_ACCESS:
        return redirect('/dashboard/')

    meetings = get_user_meetings(request.user)

    page_num = request.GET.get('page')
    pager = Paginator(meetings, 20)

    try:
        meetings = pager.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        meetings = pager.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        meetings = pager.page(pager.num_pages)

    return render(
        request,
        'content/meetings_list.html',
        {
            'meetings': meetings,
        }
    )


@login_required
@has_desktop_access
@validate_user
def meeting_player(request, meeting_id):
    user = request.user

    if not user.is_staff:
        meeting = Meeting.objects.filter(pk=meeting_id)
    else:
        meeting = get_user_meetings(user).filter(pk=meeting_id)

    meeting = meeting.first()

    if not meeting:
        raise Http404()

    return render(
        request,
        'content/meeting_player.html',
        {
            "meeting": meeting,
        }
    )


def check_meeting_referer(request, meeting_id):
    http_referer = request.META.get('HTTP_REFERER')

    if not http_referer:
        return False

    http_referer = urlparse(http_referer)
    if http_referer.netloc != request.META.get('HTTP_HOST'):
        return False

    if http_referer.path != '/meetings/%s/' % meeting_id:
        return False

    return True


@login_required
@has_desktop_access
@validate_user
def meeting_playlist(request, meeting_id):
    """
        Получение списка чанков для лекции
    """
    user = request.user

    if not user.is_staff:
        meeting = Meeting.objects.filter(pk=meeting_id)
    else:
        meeting = get_user_meetings(user).filter(pk=meeting_id)

    meeting = meeting.first()

    if not meeting:
        raise Http404()

    referer_check_passed = check_meeting_referer(request=request, meeting_id=meeting_id)

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    mph = MeetingPlayHistory(
        user=request.user,
        meeting=meeting,
        useragent=request.META.get('HTTP_USER_AGENT', ''),
        ip_addr=ip,
        referer_check=referer_check_passed
    )

    mph.save()

    if not referer_check_passed:
        return redirect('/meetings/%s/' % meeting_id)

    playlist = open(os.path.join(settings.MULTIMEDIA_ROOT, 'meetings', meeting_id, 'playlist.m3u8'), 'rb').read()
    return HttpResponse(playlist, content_type='application/vnd.apple.mpegurl')


@login_required
@has_desktop_access
@validate_user
def meeting_chunk(request, meeting_id, chunk_id):
    """
        Получение чанка лекции
    """
    user = request.user

    if not user.is_staff:
        meeting = Meeting.objects.filter(pk=meeting_id)
    else:
        meeting = get_user_meetings(user).filter(pk=meeting_id)

    meeting = meeting.first()

    if not meeting:
        raise Http404()

    referer_check_passed = check_meeting_referer(request=request, meeting_id=meeting_id)

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    mph = MeetingPlayHistory(
        user=request.user,
        meeting=meeting,
        useragent=request.META.get('HTTP_USER_AGENT', ''),
        ip_addr=ip,
        referer_check=referer_check_passed,
        item="chunk.%s" % chunk_id
    )

    mph.save()

    if not referer_check_passed:
        return redirect('/meetings/%s/' % meeting_id)

    filename = os.path.join(settings.MULTIMEDIA_ROOT, 'meetings', meeting_id, 'chunks', "%s.ts" % chunk_id)

    if os.path.isfile(filename):
        mp3content = open(filename, 'rb').read()
        return HttpResponse(mp3content, content_type='audio/mpeg')
    else:
        raise Http404()
