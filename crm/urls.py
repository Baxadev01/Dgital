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
from django.views.generic import TemplateView

from crm.views import payment_cancel, stripe_notify_view, yandex_kassa_notify_view
from crm.api.prodamus_notifications import ProdamusNotificationsAPIView

app_name = 'apps.crm'

urlpatterns = [
    url(r'^kassa/fail/$', TemplateView.as_view(template_name='kassa_fail.html'), name='kassa_payment_fail'),
    url(r'^payment-cancel/$', payment_cancel, name='paywall-cancel'),
    url(r'^kassa/success/$', TemplateView.as_view(template_name='kassa_success.html'), name='kassa_payment_success'),
    url(r'^stripe-notifications/$', stripe_notify_view, name='stripe-notifications'),
    url(r'^kassa-notifications/$', yandex_kassa_notify_view, name='kassa-notifications'),
    url(r'^prodamus-notifications/$', ProdamusNotificationsAPIView.as_view(), name='prodamus-notifications'),
]
