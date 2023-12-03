# -*- coding: utf-8 -*-
import logging
import os
import re
import shutil
from subprocess import call

from django.conf import settings
from django.core.management.base import BaseCommand

from content.models import Meeting

logger = logging.getLogger(__name__)

SEGMENT_TIME = 30  # chunks time


def rsync_copy(_from, _to):
    command = ['rclone', 'copy', _from, _to]
    call(command)


def find_meeting_mp3(search_dir_path):
    """ Ищет в папке mp3 файл митинга.

    :param search_dir_path: abs path to the folder where mp3 must be searched
    :type search_dir_path: str
    :return: abs path to meeting audio file
    :rtype: str
    """
    # ls source/*.[Mm][Pp]3 | sort -n | head -1

    files = [f for f in os.listdir(search_dir_path) if re.search(r'\.[Mm][Pp]3$', f)]
    files.sort()

    if files:
        return os.path.join(search_dir_path, files[0])
    else:
        logger.error('MP3 not found', extra={'search_dir': search_dir_path, 'files': files})


def compress(meeting_mp3_path, compressed_mp3_path):
    """ Сжимает mp3-файл в новый файл.

    :param str meeting_mp3_path: abs path to source mp3 file
    :param str compressed_mp3_path: abs path to target file
    """

    # ffmpeg -i `ls source/*.[Mm][Pp]3 | sort -n | head -1` -map 0:0 -ac 1 -q:a 9 -y source/compressed.mp3

    command = ['ffmpeg', '-i', meeting_mp3_path, '-map', '0:0', '-ac', '1', '-q:a', '9', '-y', compressed_mp3_path]
    call(command)

    return compressed_mp3_path


def make_chunks(mp3_filepath, to_folder):
    """ Разбивает mp3-файл на чанки в соответствующей папке.

    :param str mp3_filepath: abs filepath that must be chunked
    :param str to_folder: abs folder path where chunks must be stored
    """
    # fmpeg -i ./source/compressed.mp3 -acodec copy -f segment -segment_time 30
    # -segment_list playlist.m3u8 -segment_list_entry_prefix ./chunks/ -y  -segment_format mpegts 'chunks/%03d.ts'

    chunks_folder = '%s/chunks/' % to_folder

    if os.path.isdir(chunks_folder):
        shutil.rmtree(chunks_folder)

    os.makedirs(chunks_folder)

    # print " ".join(
    #     [
    #         'ffmpeg',
    #         '-i', mp3_filepath,
    #         '-acodec', 'copy',
    #         '-f', 'segment',
    #         '-segment_time', '%s' % SEGMENT_TIME,
    #         '-segment_list', '%s/playlist.m3u8' % to_folder,
    #         '-segment_list_entry_prefix', './chunks/',
    #         '-y',
    #         '-segment_format', 'mpegts', '%s%%03d.ts' % chunks_folder,
    #     ]
    # )

    call([
        'ffmpeg',
        '-i', mp3_filepath,
        '-acodec', 'copy',
        '-f', 'segment',
        '-segment_time', '%s' % SEGMENT_TIME,
        '-segment_list', '%s/playlist.m3u8' % to_folder,
        '-segment_list_entry_prefix', './chunks/',
        '-y',
        '-segment_format', 'mpegts', '%s%%03d.ts' % chunks_folder,
    ])


class Command(BaseCommand):
    """ (DEV-41) Скачивает митинг. Обрабатывает его ffmpeg-ом (сжимает, разбивает на чанки). Загружает это в облако."""
    help = "Meetings converting"

    def add_arguments(self, parser):
        parser.add_argument('meeting_id', type=int, nargs='?', default=None, help="ID of the uploaded meeting")

    @staticmethod
    def process_meeting(meeting):
        """ Запускает обработку митинга.

        :param meeting: объект митинга
        :type meeting: content.models.Meeting
        """

        meeting.status = 'PROCESSING'
        meeting.save(update_fields=['status'])

        cloud_folder = 'aws:{folder}/meetings/{meeting_id}'.format(
            folder=settings.AWS_STORAGE_BUCKET_NAME, meeting_id=meeting.id
        )
        local_folder = '{folder}/{meeting_id}'.format(
            folder=settings.MEETINGS_DIR, meeting_id=meeting.id
        )
        source_folder = '{folder}/{meeting_id}/source'.format(
            folder=settings.MEETINGS_DIR, meeting_id=meeting.id
        )
        compressed_mp3_path = os.path.join(source_folder, 'compressed.mp3')

        try:
            # 1) загружаем из облака папку митинга
            rsync_copy(_from=cloud_folder, _to=local_folder)

            # 2) находим митинг
            meeting_mp3_path = find_meeting_mp3(search_dir_path=source_folder)

            # 3) сжимаем митинг
            compress(meeting_mp3_path, compressed_mp3_path)

            # 4) разбиваем митинг на сегменты по 30 с
            make_chunks(mp3_filepath=compressed_mp3_path, to_folder=local_folder)

            # 5) загружаем все назад в облако
            rsync_copy(_from=local_folder, _to=cloud_folder)
        except Exception as e:
            logger.error(e)
            meeting.status = 'ERROR'
            fields = ['status']
        else:
            meeting.status = 'PUBLISHED'
            meeting.is_uploaded = True
            meeting.is_playable = True
            fields = ['status', 'is_uploaded', 'is_playable']

        meeting.save(update_fields=fields)

    def handle(self, *args, **options):
        meeting_id = options.get('meeting_id')

        if not meeting_id:
            # ищем все загруженные митинги
            for meeting in Meeting.objects.filter(status='UPLOADED').iterator():
                self.process_meeting(meeting)
        else:
            try:
                meeting = Meeting.objects.get(status='UPLOADED', id=meeting_id)
            except Meeting.DoesNotExist as e:
                logger.error('Meeting not found', extra={'meeting_id': meeting_id})
                raise e

            self.process_meeting(meeting)
