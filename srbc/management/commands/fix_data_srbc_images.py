# -*- coding: utf-8 -*-
import logging
import re

from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict

from srbc.models import SRBCImage, DiaryRecord

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ (DEV-173) Ищет SRBC_IMAGES с некорректными данными в image_info
    """
    help = "Find srbc_images with typo in image_info"

    def add_arguments(self, parser):
        parser.add_argument('-f', '--fix', action='store_false', help='Do changes in DB')

    def handle(self, *args, **options):
        with_fix = not options['fix']

        if with_fix:
            print('Find srbc_images with typo in image_info WITH FIX (change data in db) !!!')
        else:
            print('Find srbc_images with typo in image_info without fix (only info output)')

        weight_pattern = re.compile('Вес: [-+]?[0-9]{3}\.?[0-9]* \/ [-+]?[0-9]+\.?[0-9]*')
        value_pattern = re.compile('[0-9]{3}\.?[0-9]*')  # more then 100

        warnings = 0
        errors = 0
        fixed_ids = []
        for img in SRBCImage.objects.filter(image_type='DATA', image_info__isnull=False).iterator():
            result = weight_pattern.search(img.image_info)
            if result:
                print(('\nFound srbc_image id[%s] with typo in image_info' % img.id))

                sub_str = result.group(0)
                try:
                    value = float(value_pattern.search(sub_str).group(0))
                except (AttributeError, TypeError, ValueError):
                    warnings += 1
                    print(('-' * 80))
                    print(('\t\t[Warning]\n Wrong value for srbc_image id[%s] sub_str[%s]' % (img.id, sub_str)))
                    print(('-' * 80))
                    continue

                try:
                    diary = DiaryRecord.objects.get(user=img.user, date=img.date)
                except DiaryRecord.DoesNotExist:
                    continue

                try:
                    weight_delta_yesterday, weight_delta_start = diary.get_delta_weights
                    print(('weight_delta_yesterday: %s' % weight_delta_yesterday))
                    print(('weight_delta_start: %s' % weight_delta_start))

                    if weight_delta_start and weight_delta_yesterday:
                        weight_text = 'Вес: %+g / %+.1f' % (weight_delta_yesterday, weight_delta_start)

                        if (value / 1000) != float(weight_delta_yesterday):
                            warnings += 1
                            print(('-' * 80))
                            print(('\t\t[Warning]\n Wrong value for srbc_image id[%s] weight[%s] -> DB_weight[%s]' %
                                  (img.id, value / 1000, weight_delta_yesterday)))
                            print(('-' * 80))

                    else:
                        weight_text = 'Вес: Нет данных'

                    img.image_info = re.sub(weight_pattern, weight_text, img.image_info)

                    print(('\t sub_str with typo: %s' % sub_str))
                    print(('\t sub_str fixed    : %s' % weight_text))
                    print('\t correct image_info:')
                    print(('\t\t' + '\n\t\t'.join(img.image_info.split('\n'))))

                    if with_fix:
                        fixed_ids.append(img.id)
                        img.save(update_fields=['image_info'])
                except Exception as e:
                    errors += 1
                    print('!!!!!!!! [Error] !!!!!!!!')
                    print(e)
                    print((model_to_dict(diary)))
                    print((model_to_dict(img)))
                    print('!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('\n')
        print(('*' * 80))
        if with_fix:
            print(('Fixed ids %s' % fixed_ids))
        else:
            if warnings:
                print(('Warnings (%s) found' % warnings))
                print(('Errors (%s) found' % errors))
                print('Please, check output data to ensure fix operation.')
            else:
                print('Check output data. If all is correct then use `--fix` key to update data in DB')
        print(('*' * 80))
