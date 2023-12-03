# -*- coding: utf-8 -*-
from django.conf.urls import url

from support.views import ask_lena

app_name = 'apps.support'

urlpatterns = [
    url(r'^ask/$', ask_lena, name='ask_lena'),
]
