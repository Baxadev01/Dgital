# -*- coding: utf-8 -*-
import logging
from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand

from crm.models import Campaign

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Переводит участников в следующие чаты (промоут) и отключает уходящих"

    def handle(self, *args, **options):
        today = date.today()
        # скрипт должен отрабатывать только в день старта новой кампании
        campaign = Campaign.objects.filter(
            start_date=today
        ).first()

        if not campaign:
            return

        call_command('promote')

        call_command('deactivate_chats')

        call_command('deactivate_payments')
