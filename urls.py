# -*- coding: utf-8 -*-
"""wifit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

import debug_toolbar
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.conf import settings
from django.conf.urls import include, url, re_path
from django.contrib import admin

from django.views.static import serve

from schema import schema_view

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^markdownx/', include('markdownx.urls')),
    url(r'^', include('django_telegrambot.urls')),
    url(r'^', include('social_django.urls', namespace='social')),

    url(r'^', include('support.urls', namespace='support')),
    url(r'^', include('srbc.urls.web', namespace='srbc')),
    url(r'^', include('content.urls.web', namespace='content')),
    url(r'^', include('crm.urls', namespace='crm')),

    url(r'^api/v1/', include('srbc.urls.api.v1', namespace='v1')),
    url(r'^api/v1/', include('content.urls.api.v1', namespace='v1')),
    url(r'^api/v2/', include('srbc.urls.api.v2', namespace='v2')),
    url(r'^api/v3/', include('srbc.urls.api.v3', namespace='v3')),
    url(r'^api/v3/', include('content.urls.api.v3', namespace='v3')),

    url(r'^paypal/', include(('paypal.standard.ipn.urls', 'paypal'), namespace='paypal')),
    url(r'^api/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns = [
        url(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ] + staticfiles_urlpatterns() + urlpatterns

urlpatterns = [
    url(r'^__debug__/', include(debug_toolbar.urls)),
] + urlpatterns
