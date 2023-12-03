# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.core.management import call_command
from srbc.models import Profile
from django.db import connection, OperationalError, InterfaceError

import logging

from time import sleep

# from decimal import Decimal

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Watches profiles and updates Instagram on request"

    def handle(self, *args, **options):
        while True:
            try:
                profiles_to_update = Profile.objects.filter(instagram_update_required=True).all()
            except (OperationalError, InterfaceError):
                connection.close()
                continue

            for profile_to_update in profiles_to_update:
                logger.info('Found user to update instagram: %s' % profile_to_update.user_id)
                call_command('ig_load', user=profile_to_update.user_id)
                profile_to_update.instagram_update_required = False
                try:
                    profile_to_update.save()
                except (OperationalError, InterfaceError):
                    connection.close()
                    profile_to_update.save()

            sleep(1)
