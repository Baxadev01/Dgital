# -*- coding: utf-8 -*-
from django.conf.urls import url

from content.views.api import (RecipeListAPIView, manual_download_api, meeting_playlist_api, meeting_chunk_api)
app_name = 'apps.content_api'

urlpatterns = [
    url(
        r'^content/recipes/$', 
        RecipeListAPIView.as_view(), 
        name='api-articles-item'
    ),

    url(r'^manual/$', manual_download_api, name='manual-download-link-api'),
    url(r'^meetings/(?P<meeting_id>[0-9]+)/playlist.m3u8$', meeting_playlist_api, name='meeting-playlist-api'),
    url(r'^meetings/(?P<meeting_id>[0-9]+)/chunks/(?P<chunk_id>[0-9]+).ts$', meeting_chunk_api, name='meeting-chunk-api'),
    
]
