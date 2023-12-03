# -*- coding: utf-8 -*-
from django.shortcuts import redirect, render


def subscription_form_news(request):
    return render(
        request,
        'content/subscription_news.html'
    )


def subscription_form_admission(request):
    return render(
        request,
        'content/subscription_admission.html'
    )
