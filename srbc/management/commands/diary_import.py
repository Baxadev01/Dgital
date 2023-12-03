from django.core.management.base import BaseCommand, CommandError
from srbc.models import Profile, User, DiaryRecord
import csv


class Command(BaseCommand):
    help = "Imports diaries from stated CSV file"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            f = open(options['filename'], 'r')
        except Exception as e:
            raise CommandError('Couldn\'t open file')
