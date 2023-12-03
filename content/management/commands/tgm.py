# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand
from lockfile import locked

from content.tgmails import sender as tgm_sender

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sending SendMail to TG"

    def add_arguments(self, parser):
        parser.add_argument('-d', '--debug', action='store_true', help='Do not send mails. Show DEBUG info.')

    @locked('/tmp/srbc_content_tgm.lock', 0)
    def handle(self, *args, **options):
        debug_mode = options.get('debug', False)

        tgm_sender.collect(for_debug=debug_mode)

        if debug_mode:
            print('Can be processed: %s ' % tgm_sender.mailing_objects)
            print('Users to send mails:')
            print(tgm_sender.debug_info)
            exit()
