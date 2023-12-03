# -*- coding: utf-8 -*-
from support.models import Ticket

from django.http.response import Http404
from django.shortcuts import redirect, render
from support.forms import TicketForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from srbc.decorators import validate_user
from django.contrib.auth.decorators import login_required, user_passes_test
import os
import mimetypes
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
from django.conf import settings
from hashlib import sha224


def ask_lena(request):
    new_ticket = None
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():

            new_ticket = form.save(commit=False)
            if request.user.is_authenticated:
                new_ticket.user = request.user

            signature = "%s|%s|%s|%s" % (
                sha224(new_ticket.full_name.strip().encode('UTF-8')).hexdigest(),
                sha224(new_ticket.email.strip().encode('UTF-8')).hexdigest(),
                sha224(new_ticket.subject.strip().encode('UTF-8')).hexdigest(),
                sha224(new_ticket.body.strip().encode('UTF-8')).hexdigest(),
            )

            signature = sha224(signature.encode()).hexdigest()
            new_ticket.signature = signature

            if not Ticket.objects.filter(signature=signature).exists():
                new_ticket.save()

    else:
        instance = {}
        if request.user.is_authenticated and request.user.email:
            instance['email'] = request.user.email
            instance['full_name'] = '%s %s' % (request.user.first_name, request.user.last_name)
            instance['full_name'] = instance['full_name'].strip()

        form = TicketForm(initial=instance)

    return render(
        request,
        'support/ask_form.html',
        {
            'form': form,
            # 'pager': pager,
            'ticket': new_ticket,
        }
    )
