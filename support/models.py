# -*- coding: utf-8 -*-
import os
from uuid import uuid4, uuid5, NAMESPACE_OID
from django.db import models
from django.contrib.auth.models import User
from social_django.models import UserSocialAuth
from markdownx.models import MarkdownxField
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from decimal import Decimal
from django.contrib.postgres.fields import ArrayField
from datetime import date, datetime


class Ticket(models.Model):
    user = models.ForeignKey(User, null=True, related_name="tickets", blank=True, on_delete=models.SET_NULL)
    full_name = models.CharField(max_length=512)
    email = models.CharField(max_length=512)
    subject = models.TextField(max_length=100)
    body = models.TextField()

    assignee = models.ForeignKey(
        User, related_name="assigned_tickets", blank=True, null=True,
        limit_choices_to={'groups__name': "Feedback Manager"}, on_delete=models.SET_NULL
    )

    status = models.CharField(blank=True, default='NEW', max_length=20, choices=(
        ('NEW', 'Новый'),
        ('ASSIGNED', 'В работе'),
        ('RESOLVED', 'Отвечен'),
        ('REJECTED', 'Отклонен'),
    ))
    posted_at = models.DateTimeField(auto_now_add=True)
    signature = models.CharField(max_length=64)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.pk)

    class Meta:
        indexes = [
            models.Index(fields=['signature']),
            models.Index(fields=['posted_at']),
            models.Index(fields=['assignee']),
            models.Index(fields=['status']),
        ]
