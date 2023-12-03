# -*- coding: utf-8 -*-
import logging
from uuid import uuid4

from PIL import Image
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from srbc.models import SRBCImage, DiaryRecord
from srbc.utils.srbc_image import put_image_in_memory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ (DEV-174):
    1) обнуляет значения в базе для изображений с типом DATA (удаляет файлы из хранилища)
    2) генерирует MD-изображение (600х600) для тех изображений, у которых его нет
    """
    help = "Removes `DATA` images and generates MD-images"

    def add_arguments(self, parser):
        parser.add_argument('-p', '--process', action='store_true', help='Do changes in DB')
        parser.add_argument('-rd', '--remove_data_images', action='store_true', help='Remove `data` SRBCImages')
        parser.add_argument('-md', '--generate_md_thumbs', action='store_true', help='Generate MD thumbnail')

    def handle(self, *args, **options):
        info_mode = not options['process']
        remove_data_images = options['remove_data_images']
        generate_md_thumbs = options['generate_md_thumbs']

        if remove_data_images:
            self.process_data_images(info_mode)

        if generate_md_thumbs:
            self.process_md_thumbs(info_mode)

    @staticmethod
    def process_data_images(info_mode=True):
        print('Process DATA-images ')
        # ищем DATA-изобажеия
        # удаляем миниатюры из хранилища
        # удаляем большую картинку из хранилищца
        for data_image in SRBCImage.objects.filter(image_type='DATA').iterator():
            # изображения из AWS надо удалять напрямую (проверно через storage.exists(...))

            if data_image.thumbnail:
                print(('\t Delete thumb for SRBCImage with id %s' % data_image.id))
                if not info_mode:
                    data_image.thumbnail.delete()

            if data_image.image:
                print(('\t Delete image for SRBCImage with id %s' % data_image.id))
                if not info_mode:
                    data_image.image.delete()

    @staticmethod
    def process_md_thumbs(info_mode=True):
        print('Process MD thumbs')
        # генерируем MD-изобажение для тех изображений, у которых его нет
        # заменяем файбнейл у изображений на MD
        for srbc_image in SRBCImage.objects.iterator():
            print(('- Process SRBCImage with id %s' % srbc_image.id))
            if srbc_image.image:
                # удаляем текущий фамбнейл
                if srbc_image.thumbnail:
                    is_md_thumb = False
                    with Image.open(ContentFile(srbc_image.thumbnail.read())) as thumb_img:
                        if thumb_img.width == thumb_img.height == 600:
                            # миниатюры уже в MD
                            is_md_thumb = True

                    if is_md_thumb:
                        print('\t Already MD-thumb')
                        continue
                    else:
                        if not info_mode:
                            print('\t Delete thumb for SRBCImage')
                            srbc_image.thumbnail.delete()
                        else:
                            print('\t Need to delete thumb for SRBCImage')

                # получаем большое изображение и генерим для него новый фамбнейл (600x600)
                img_raw = srbc_image.image.read()
                with Image.open(ContentFile(img_raw)) as img:
                    w, h = img.width, img.height
                    filename = str(uuid4())

                    if w > 600:
                        # ресайзим до 600x600
                        print('\t Need to resize thumb')
                        if not info_mode:
                            thumbnail = img.resize((600, 600), Image.ANTIALIAS)
                    else:
                        print('\t Use `image` as thumb')
                        thumbnail = img.copy()

                    if not info_mode:
                        srbc_image.thumbnail = put_image_in_memory(image=thumbnail, filename="tn_%s" % filename)
                        srbc_image.save(update_fields=['thumbnail'])
            else:
                logger.error('No image for SRBCImage with id %s' % srbc_image.id)
