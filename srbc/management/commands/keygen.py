# -*- coding: utf-8 -*-

import logging
import string
from random import choice

from django.core.management.base import BaseCommand

from srbc.models import Wave, Invitation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generates invitation codes"

    def add_arguments(self, parser):
        parser.add_argument('--mode', action='store', dest='mode', type=str)
        parser.add_argument('--wave', action='store', dest='wave', type=int, nargs='?')
        parser.add_argument('--count', action='store', dest='count', type=int, nargs='?', default=1)
        parser.add_argument('--days', action='store', dest='days', type=int, nargs='?', default=58)

    def handle(self, *args, **options):
        wave_id = options.get('wave')
        codes_count = options.get('count', 1)
        code_duration = options.get('days')
        communication_mode = options.get('mode')

        wave = Wave.objects.filter(pk=wave_id).first()

        if communication_mode not in ['CHAT', 'CHANNEL']:
            print("Incorrect communication mode")
            return

        if wave:
            wave_title_split = wave.title.split('.')

            if len(wave_title_split) == 1:
                wave_title = wave.title.zfill(3)
            else:
                wave_title = '%s%s' % (wave_title_split[0], wave_title_split[1].zfill(2))

        else:
            wave_title = communication_mode

        allchar = string.ascii_letters + string.digits

        codes = []
        for i in range(codes_count):
            code = Invitation()
            code.wave = wave
            code.days_paid = code_duration
            code.communication_mode = communication_mode

            code_string = None
            while code_string is None or code_string in codes:
                code_string = 'SRBC-%s-%s' % (wave_title, "".join(choice(allchar) for x in range(12)).upper())
            code.code = code_string
            code.save()
            print(code.code)
