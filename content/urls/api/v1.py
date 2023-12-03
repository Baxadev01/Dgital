# -*- coding: utf-8 -*-
from django.conf.urls import url

from content.views.api import (TgMessagesViewSet, TgPostsViewSet, TgChannelsViewSet, TgUsersViewSet, UsersChatSet,
                               MeetingsViewSet, ArticleSet)
app_name = 'apps.content_api'

urlpatterns = [
    url(
        r'^tg/messages/(?P<message_id>[0-9]+)/$',
        TgMessagesViewSet.as_view(
            {
                "get": "get_one",
                "put": "update_one"
            }),
        name='tg-messages-item'
    ),
    url(r'^tg/messages/$',
        TgMessagesViewSet.as_view(
            {
                "get": "list",
                "put": "respond",
            }
        ),
        name='tg-messages-list'),
    url(r'^tg/channels/$',
        TgChannelsViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name='tg-channels-list'),

    url(r'^tg/users/$',
        TgUsersViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name='tg-users-list'),

    url(r'^tg/posts/(?P<post_id>[0-9]+)/$',
        TgPostsViewSet.as_view(
            {
                "get": "get_one",
                "put": "update_one",
            }
        ),
        name='tg-posts-item'),
    url(r'^tg/posts/$',
        TgPostsViewSet.as_view(
            {
                "get": "list",
                "post": "add",
            }
        ), name='tg-posts-list'),

    url(
        r'chat/(?P<chat_id>[0-9]+)/notify/$', UsersChatSet.as_view(
            {
                "head": "notify_user",
            }),
        name='user-chat-set-notify'
    ),

    url(
        r'content/meetings/$', MeetingsViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name='api-meetings-list'
    ),

    url(
        r'^content/articles/$', ArticleSet.as_view(
            {
                "get": "get_articles",
            }
        ), name='api-articles-list'
    ),
    url(
        r'^content/articles/(?P<article_id>[0-9]+)/$', ArticleSet.as_view(
            {
                "get": "get_article",
            }
        ), name='api-articles-item'
    ),
]
