# -*- coding: utf-8 -*-
from django.conf.urls import url

from content.views.admin import channel_admin, sendmail_admin
from content.views.lp import subscription_form_news, subscription_form_admission
from content.views.meetings import meeting_chunk, meeting_player, meeting_playlist, meetings_list
from content.views.participant import articles_list, article_page
from content.views.participant import index, recipes_list, tos, tos_ru, tos_ee, privacy_en, manual_download

app_name = 'apps.content'

urlpatterns = [
    url(r'^manual/$', manual_download, name='manual-download-link'),
    url(r'^tos/$', tos, name='tos-page'),
    url(r'^tos-ru/$', tos_ru, name='tos-page-ru'),
    url(r'^tos-ee/$', tos_ee, name='tos-page-ee'),
    url(r'^privacy/$', privacy_en, name='privacy-page-en'),
    url(r'^recipes/$', recipes_list, name='recipes-list'),
    url(r'^articles/$', articles_list, name='articles-list'),
    url(r'^articles/(?P<article_slug>[a-zA-Z0-9_-]+)/$', article_page, name='article-page'),
    url(r'^subscribe/news/$', subscription_form_news, name='lp-news'),
    url(r'^subscribe/admission/$', subscription_form_admission, name='lp-admission'),

    url(r'^meetings/$', meetings_list, name='meetings-list'),
    url(r'^meetings/(?P<meeting_id>[0-9]+)/$', meeting_player, name='meeting-player'),
    url(r'^meetings/(?P<meeting_id>[0-9]+)/playlist.m3u8$', meeting_playlist, name='meeting-playlist'),
    url(r'^meetings/(?P<meeting_id>[0-9]+)/chunks/(?P<chunk_id>[0-9]+).ts$', meeting_chunk, name='meeting-chunk'),

    url(r'^channel/$', channel_admin, name='channel'),
    url(r'^staff/sendmail/$', sendmail_admin, name='sendmail'),

    url(r'^$', index, name='index-page'),
]
