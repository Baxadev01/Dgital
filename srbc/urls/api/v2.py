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

from django.conf.urls import url

from srbc.views.api.v2.diary import DiaryMealSet

# FIXME
app_name = 'apps.srbc_api'

urlpatterns = [
    url(
        r'^diary/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meals/image/(?P<meal_dt>[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}:[0-9]{2})/$',
        DiaryMealSet.as_view(
            {
                "put": "meals_images_upsert",
                "delete": "meals_images_delete",
            }),
        name='diary-meals-images-item'
    ),
    # FIXME удалить потом, как добавится еще урлы, а то форматирует криво )))
]
