# -*- coding: utf-8 -*-
import io
import base64
import datetime
import logging
import math
import os
from uuid import uuid4

import pytz
from PIL import Image, ImageFile, ImageFont, ImageDraw, ExifTags
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from pilkit.processors import ResizeToFill, AddBorder

from srbc.models import SRBCImage, DiaryMeal, MealProduct, MealComponent

logger = logging.getLogger('IMAGES_API')

ImageFile.MAXBLOCK = 2 ** 20


def build_compare_collages(base_checkpoint_photo, checkpoint_photo):
    """ Создает изображения коллажа относительно базового коллажа.

    :param base_checkpoint_photo:
    :type base_checkpoint_photo: srbc.models.CheckpointPhotos
    :param checkpoint_photo:
    :type checkpoint_photo: srbc.models.CheckpointPhotos
    :return: list of SRBCImage objects
    :rtype: list(srbc.models.SRBCImage)
    """
    collage_section_width = 600
    collage_section_height = 1080

    crop_meta = checkpoint_photo.crop_meta

    if 'front' not in crop_meta or 'side' not in crop_meta or 'rear' not in crop_meta:
        raise ValueError("Не все проекции коллажа настроены")

    base_crop_meta = base_checkpoint_photo.crop_meta
    if 'front' not in base_crop_meta or 'side' not in base_crop_meta or 'rear' not in base_crop_meta:
        raise ValueError("Не все проекции базового коллажа настроены")

    images = {
        'front': Image.open(checkpoint_photo.front_image),
        'side': Image.open(checkpoint_photo.side_image),
        'rear': Image.open(checkpoint_photo.rear_image),
    }

    base_images = {
        'front': Image.open(base_checkpoint_photo.front_image),
        'side': Image.open(base_checkpoint_photo.side_image),
        'rear': Image.open(base_checkpoint_photo.rear_image),
    }

    meta_data = checkpoint_photo.crop_meta
    base_meta_data = base_checkpoint_photo.crop_meta

    result_collages = []

    for projection in ['front', 'side', 'rear']:
        projection_crop = meta_data.get(projection).get('crop')
        base_projection_crop = base_meta_data.get(projection).get('crop')

        projection_scale = 1
        base_projection_scale = 1

        if projection_crop.get('width') < collage_section_width \
                and projection_crop.get('height') < collage_section_height:
            projection_scale = min(collage_section_width * 1. / projection_crop.get('width'),
                                   collage_section_height * 1. / projection_crop.get('height'))

        if base_projection_crop.get('width') < collage_section_width \
                and base_projection_crop.get('height') < collage_section_height:
            base_projection_scale = min(collage_section_width * 1. / base_projection_crop.get('width'),
                                        collage_section_height * 1. / base_projection_crop.get('height'))

        projection_delta = (meta_data.get(projection).get('kneeline')
                            - meta_data.get(projection).get('eyeline')) * projection_scale
        base_projection_delta = (base_meta_data.get(projection).get('kneeline')
                                 - base_meta_data.get(projection).get('eyeline')) * base_projection_scale

        min_delta = min(projection_delta, base_projection_delta)

        projection_delta_scale = 1.0 * min_delta / projection_delta
        base_projection_delta_scale = 1.0 * min_delta / base_projection_delta

        projection_head = (meta_data.get(projection).get('eyeline')
                           - meta_data.get(projection).get('crop').get('top')) * projection_scale
        projection_head_adjusted = projection_head * projection_delta_scale

        base_projection_head = (base_meta_data.get(projection).get('eyeline')
                                - base_meta_data.get(projection).get('crop').get('top')) * base_projection_scale
        base_projection_head_adjusted = base_projection_head * base_projection_delta_scale

        max_head = max(projection_head_adjusted, base_projection_head_adjusted)

        projection_leg = (meta_data.get(projection).get('crop').get('top')
                          + meta_data.get(projection).get('crop').get('height')
                          - meta_data.get(projection).get('kneeline')) * projection_scale
        projection_leg_adjusted = projection_leg * projection_delta_scale

        base_projection_leg = (base_meta_data.get(projection).get('crop').get('top')
                               + base_meta_data.get(projection).get('crop').get('height')
                               - base_meta_data.get(projection).get('kneeline')) * base_projection_scale

        base_projection_leg_adjusted = base_projection_leg * base_projection_delta_scale

        max_leg = max(projection_leg_adjusted, base_projection_leg_adjusted, )

        section_height = max_leg + max_head + min_delta

        if section_height < collage_section_height:
            height_delta = (collage_section_height - section_height) / 2

            projection_head_adjusted += height_delta
            base_projection_head_adjusted += height_delta

            projection_leg_adjusted += height_delta
            base_projection_leg_adjusted += height_delta

            section_height = collage_section_height

        section_width = collage_section_width * section_height / collage_section_height

        max_width = max(
            projection_crop.get('width') * projection_delta_scale * projection_scale,
            base_projection_crop.get('width') * base_projection_delta_scale * base_projection_scale,
        )

        if max_width > section_width:
            height_delta = (max_width - section_width) / 2 * collage_section_height / collage_section_width

            projection_head_adjusted += height_delta
            base_projection_head_adjusted += height_delta

            projection_leg_adjusted += height_delta
            base_projection_leg_adjusted += height_delta

            section_height += 2 * height_delta
            section_width = max_width

        projection_real_height = projection_delta + (max_head + max_leg) / projection_delta_scale
        base_projection_real_height = base_projection_delta + (max_head + max_leg) / base_projection_delta_scale

        projection_real_width = section_width * projection_real_height / section_height
        base_projection_real_width = section_width * base_projection_real_height / section_height

        projection_crop_corner_top = meta_data.get(projection).get('crop').get('top') \
                                     + projection_head / projection_scale - max_head / (
                                             projection_delta_scale * projection_scale)

        projection_crop_corner_left = meta_data.get(projection).get('crop').get('left') \
                                      + meta_data.get(projection).get('crop').get('width') / 2 \
                                      - projection_real_width / (2 * projection_scale)

        base_projection_crop_corner_top = base_meta_data.get(projection).get('crop').get('top') \
                                          + base_projection_head / base_projection_scale - max_head / (
                                                  base_projection_delta_scale * base_projection_scale)

        base_projection_crop_corner_left = base_meta_data.get(projection).get('crop').get('left') \
                                           + base_meta_data.get(projection).get('crop').get('width') / 2 \
                                           - base_projection_real_width / (2 * base_projection_scale)

        projection_initial_width, projection_initial_height = images[projection].size
        base_projection_initial_width, base_projection_initial_height = base_images[projection].size

        images[projection] = images[projection].rotate(-1 * meta_data.get(projection).get('angle'), expand=True)
        base_images[projection] = base_images[projection].rotate(-1 * base_meta_data.get(projection).get('angle'),
                                                                 expand=True)

        projection_rotated_width, projection_rotated_height = images[projection].size
        base_projection_rotated_width, base_projection_rotated_height = base_images[projection].size

        # Alter coordinates after rotation (based on image center)

        projection_crop_corner_left = projection_crop_corner_left - projection_initial_width / 2 + projection_rotated_width / 2
        projection_crop_corner_top = projection_crop_corner_top - projection_initial_height / 2 + projection_rotated_height / 2

        base_projection_crop_corner_left = base_projection_crop_corner_left - base_projection_initial_width / 2 + base_projection_rotated_width / 2
        base_projection_crop_corner_top = base_projection_crop_corner_top - base_projection_initial_height / 2 + base_projection_rotated_height / 2

        cropped_projection = images[projection].crop(
            (
                math.floor(projection_crop_corner_left),
                math.floor(projection_crop_corner_top),
                math.floor(projection_crop_corner_left) + math.ceil(projection_real_width / projection_scale),
                math.floor(projection_crop_corner_top) + math.ceil(projection_real_height / projection_scale),
            )
        )

        cropped_base_projection = base_images[projection].crop(
            (
                math.floor(base_projection_crop_corner_left),
                math.floor(base_projection_crop_corner_top),
                math.floor(base_projection_crop_corner_left) + math.ceil(
                    base_projection_real_width / base_projection_scale),
                math.floor(base_projection_crop_corner_top) + math.ceil(
                    base_projection_real_height / base_projection_scale),
            )
        )

        # projection_measurements = {
        #     'delta': projection_delta,
        #     'delta_scale': projection_delta_scale,
        #     'head': projection_head,
        #     'head_adj': projection_head_adjusted,
        #     'leg': projection_leg,
        #     'leg_adj': projection_leg_adjusted,
        #     'real_height': projection_real_height,
        #     'real_width': projection_real_width,
        #     'crop_top': projection_crop_corner_top,
        #     'crop_left': projection_crop_corner_left,
        # }
        #
        # base_projection_measurements = {
        #     'delta': base_projection_delta,
        #     'delta_scale': base_projection_delta_scale,
        #     'head': base_projection_head,
        #     'head_adj': base_projection_head_adjusted,
        #     'leg': base_projection_leg,
        #     'leg_adj': base_projection_leg_adjusted,
        #     'real_height': base_projection_real_height,
        #     'real_width': base_projection_real_width,
        #     'crop_top': base_projection_crop_corner_top,
        #     'crop_left': base_projection_crop_corner_left,
        # }
        #
        # logger.info('base: %s' % base_projection_measurements)
        # logger.info('last: %s' % projection_measurements)

        if projection_scale != 1:
            new_projection_size = tuple([int(x * projection_scale) for x in cropped_projection.size])
            cropped_projection = cropped_projection.resize(new_projection_size)

        if base_projection_scale != 1:
            new_base_projection_size = tuple([int(x * base_projection_scale) for x in cropped_base_projection.size])
            cropped_base_projection = cropped_base_projection.resize(new_base_projection_size)

        cropped_projection.thumbnail((collage_section_width, collage_section_height), Image.ANTIALIAS)
        cropped_base_projection.thumbnail((collage_section_width, collage_section_height), Image.ANTIALIAS)

        collage = Image.new('RGB', (2 * collage_section_width, 2 * collage_section_width))
        collage.paste(cropped_base_projection, (0, 0))
        collage.paste(cropped_projection, (collage_section_width, 0))

        path_to_assets = os.path.join(settings.BASE_DIR, "srbc", "assets", "collage_data")

        path_to_font = os.path.join(path_to_assets, "days.ttf")
        img_font = ImageFont.truetype(path_to_font, 90)
        font_color = (255, 255, 255)

        template_draw = ImageDraw.Draw(collage)

        collage_date = checkpoint_photo.date.__format__("%d.%m.%Y")
        date_dimension = template_draw.textsize(collage_date, img_font)

        base_collage_date = base_checkpoint_photo.date.__format__("%d.%m.%Y")
        base_date_dimension = template_draw.textsize(base_collage_date, img_font)

        text_x = collage_section_width * 3 / 2 - date_dimension[0] / 2
        text_y = collage_section_height

        template_draw.text(xy=(text_x, text_y), text=collage_date, fill=font_color, font=img_font)

        text_x = collage_section_width * 1 / 2 - base_date_dimension[0] / 2
        text_y = collage_section_height

        template_draw.text(xy=(text_x, text_y), text=base_collage_date, fill=font_color, font=img_font)

        inmemory_file = put_image_in_memory(collage, '%s-%s' % (projection, str(uuid4().hex)))

        thumbnail = collage.resize((600, 600), Image.ANTIALIAS)

        thumbnail_inmemory_file = put_image_in_memory(thumbnail, 'tn_%s-%s' % (projection, str(uuid4().hex)))

        result = save_image(
            user=checkpoint_photo.user,
            date=checkpoint_photo.date,
            image_type='CHECKPOINT_PHOTO_%s' % projection.upper(),
            image_file=inmemory_file,
            thumbnail_file=thumbnail_inmemory_file,
            is_published=True
        )
        result_collages.append(result)

    return result_collages


def build_3view_collage(checkpoint_photo):
    """ Генерирует коллаж в трёх проекциях для CheckpointPhotos

    :param checkpoint_photo:
    :type checkpoint_photo: srbc.models.CheckpointPhotos

    :return: list of SRBCImage objects or None (in case of error)
    :rtype: list(srbc.models.SRBCImage)
    """

    collage_section_width = 400
    collage_section_height = 1080

    crop_meta = checkpoint_photo.crop_meta

    if 'front' not in crop_meta or 'side' not in crop_meta or 'rear' not in crop_meta:
        raise ValueError("Не все проекции настроены")

    image_front = Image.open(checkpoint_photo.front_image)
    image_side = Image.open(checkpoint_photo.side_image)
    image_rear = Image.open(checkpoint_photo.rear_image)

    meta_data = checkpoint_photo.crop_meta

    front_delta = meta_data.get('front').get('kneeline') - meta_data.get('front').get('eyeline')
    side_delta = meta_data.get('side').get('kneeline') - meta_data.get('side').get('eyeline')
    rear_delta = meta_data.get('rear').get('kneeline') - meta_data.get('rear').get('eyeline')

    min_delta = min(front_delta, side_delta, rear_delta)

    front_delta_scale = 1.0 * min_delta / front_delta
    side_delta_scale = 1.0 * min_delta / side_delta
    rear_delta_scale = 1.0 * min_delta / rear_delta

    front_head = meta_data.get('front').get('eyeline') - meta_data.get('front').get('crop').get('top')
    front_head_adjusted = front_head * front_delta_scale

    side_head = meta_data.get('side').get('eyeline') - meta_data.get('side').get('crop').get('top')
    side_head_adjusted = side_head * side_delta_scale

    rear_head = meta_data.get('rear').get('eyeline') - meta_data.get('rear').get('crop').get('top')
    rear_head_adjusted = rear_head * rear_delta_scale

    max_head = max(front_head_adjusted, side_head_adjusted, rear_head_adjusted)

    front_leg = meta_data.get('front').get('crop').get('top') + meta_data.get('front').get('crop').get('height') \
                - meta_data.get('front').get('kneeline')
    front_leg_adjusted = front_leg * front_delta_scale

    side_leg = meta_data.get('side').get('crop').get('top') + meta_data.get('side').get('crop').get('height') \
               - meta_data.get('side').get('kneeline')
    side_leg_adjusted = side_leg * side_delta_scale

    rear_leg = meta_data.get('rear').get('crop').get('top') + meta_data.get('rear').get('crop').get('height') \
               - meta_data.get('rear').get('kneeline')
    rear_leg_adjusted = rear_leg * rear_delta_scale

    max_leg = max(front_leg_adjusted, side_leg_adjusted, rear_leg_adjusted)

    section_height = max_leg + max_head + min_delta

    if section_height < collage_section_height:
        height_delta = (collage_section_height - section_height) / 2

        front_head_adjusted += height_delta
        side_head_adjusted += height_delta
        rear_head_adjusted += height_delta

        front_leg_adjusted += height_delta
        side_leg_adjusted += height_delta
        rear_leg_adjusted += height_delta

        section_height = collage_section_height

    section_width = collage_section_width * section_height / collage_section_height

    max_width = max(
        meta_data.get('front').get('crop').get('width') * front_delta_scale,
        meta_data.get('side').get('crop').get('width') * side_delta_scale,
        meta_data.get('rear').get('crop').get('width') * rear_delta_scale
    )

    if max_width > section_width:
        height_delta = (max_width - section_width) / 2 * collage_section_height / collage_section_width

        front_head_adjusted += height_delta
        side_head_adjusted += height_delta
        rear_head_adjusted += height_delta

        front_leg_adjusted += height_delta
        side_leg_adjusted += height_delta
        rear_leg_adjusted += height_delta

        section_height += 2 * height_delta
        section_width = max_width

    front_real_height = front_delta + (max_head + max_leg) / front_delta_scale
    side_real_height = side_delta + (max_head + max_leg) / side_delta_scale
    rear_real_height = rear_delta + (max_head + max_leg) / rear_delta_scale

    front_real_width = section_width * front_real_height / section_height
    side_real_width = section_width * side_real_height / section_height
    rear_real_width = section_width * rear_real_height / section_height

    front_crop_corner_top = meta_data.get('front').get('crop').get('top') \
                            + front_head - max_head / front_delta_scale

    front_crop_corner_left = meta_data.get('front').get('crop').get('left') \
                             + meta_data.get('front').get('crop').get('width') / 2 - front_real_width / 2

    side_crop_corner_top = meta_data.get('side').get('crop').get('top') \
                           + side_head - max_head / side_delta_scale

    side_crop_corner_left = meta_data.get('side').get('crop').get('left') \
                            + meta_data.get('side').get('crop').get('width') / 2 - side_real_width / 2

    rear_crop_corner_top = meta_data.get('rear').get('crop').get('top') \
                           + rear_head - max_head / rear_delta_scale

    rear_crop_corner_left = meta_data.get('rear').get('crop').get('left') \
                            + meta_data.get('rear').get('crop').get('width') / 2 - rear_real_width / 2

    image_front_initial_width, image_front_initial_height = image_front.size
    image_side_initial_width, image_side_initial_height = image_side.size
    image_rear_initial_width, image_rear_initial_height = image_rear.size

    image_front = image_front.rotate(-1 * meta_data.get('front').get('angle'), expand=True)
    image_side = image_side.rotate(-1 * meta_data.get('side').get('angle'), expand=True)
    image_rear = image_rear.rotate(-1 * meta_data.get('rear').get('angle'), expand=True)

    image_front_rotated_width, image_front_rotated_height = image_front.size
    image_side_rotated_width, image_side_rotated_height = image_side.size
    image_rear_rotated_width, image_rear_rotated_height = image_rear.size

    # image_front.save('front_rotated.jpg', 'JPEG', quality=80, optimize=True, progressive=True)
    # Alter coordinates after rotation (based on image center)

    front_crop_corner_left = front_crop_corner_left - image_front_initial_width / 2 + image_front_rotated_width / 2
    front_crop_corner_top = front_crop_corner_top - image_front_initial_height / 2 + image_front_rotated_height / 2

    side_crop_corner_left = side_crop_corner_left - image_side_initial_width / 2 + image_side_rotated_width / 2
    side_crop_corner_top = side_crop_corner_top - image_side_initial_height / 2 + image_side_rotated_height / 2

    rear_crop_corner_left = rear_crop_corner_left - image_rear_initial_width / 2 + image_rear_rotated_width / 2
    rear_crop_corner_top = rear_crop_corner_top - image_rear_initial_height / 2 + image_rear_rotated_height / 2

    # logger.info(
    #     "Front Crop coordinates: %s" % [
    #         math.floor(front_crop_corner_left),
    #         math.floor(front_crop_corner_top),
    #         math.floor(front_crop_corner_left) + math.ceil(front_real_width),
    #         math.floor(front_crop_corner_top) + math.ceil(front_real_height),
    #     ]
    # )

    cropped_front = image_front.crop(
        (
            math.floor(front_crop_corner_left),
            math.floor(front_crop_corner_top),
            math.floor(front_crop_corner_left) + math.ceil(front_real_width),
            math.floor(front_crop_corner_top) + math.ceil(front_real_height),
        )
    )

    cropped_side = image_side.crop(
        (
            math.floor(side_crop_corner_left),
            math.floor(side_crop_corner_top),
            math.floor(side_crop_corner_left) + math.ceil(side_real_width),
            math.floor(side_crop_corner_top) + math.ceil(side_real_height),
        )
    )

    cropped_rear = image_rear.crop(
        (
            math.floor(rear_crop_corner_left),
            math.floor(rear_crop_corner_top),
            math.floor(rear_crop_corner_left) + math.ceil(rear_real_width),
            math.floor(rear_crop_corner_top) + math.ceil(rear_real_height),
        )
    )

    # cropped_front.save('front_cropped.jpg', 'JPEG', quality=80, optimize=True, progressive=True)

    front_scale = 1.0 * section_height / front_real_height
    side_scale = 1.0 * section_height / side_real_height
    rear_scale = 1.0 * section_height / rear_real_height

    if front_scale != 1:
        new_front_size = tuple([int(x * front_scale) for x in cropped_front.size])
        cropped_front = cropped_front.resize(new_front_size)

    if side_scale != 1:
        new_side_size = tuple([int(x * side_scale) for x in cropped_side.size])
        cropped_side = cropped_side.resize(new_side_size)

    if rear_scale != 1:
        new_rear_size = tuple([int(x * rear_scale) for x in cropped_rear.size])
        cropped_rear = cropped_rear.resize(new_rear_size)

    cropped_front.thumbnail((collage_section_width, collage_section_height), Image.ANTIALIAS)
    cropped_side.thumbnail((collage_section_width, collage_section_height), Image.ANTIALIAS)
    cropped_rear.thumbnail((collage_section_width, collage_section_height), Image.ANTIALIAS)

    collage = Image.new('RGB', (3 * collage_section_width, 3 * collage_section_width))
    collage.paste(cropped_front, (0, 0))
    collage.paste(cropped_side, (collage_section_width, 0))
    collage.paste(cropped_rear, (2 * collage_section_width, 0))

    path_to_assets = os.path.join(settings.BASE_DIR, "srbc", "assets", "collage_data")

    path_to_font = os.path.join(path_to_assets, "days.ttf")
    img_font = ImageFont.truetype(path_to_font, 120)
    font_color = (255, 255, 255)

    collage_date = checkpoint_photo.date.__format__("%d.%m.%Y")
    template_draw = ImageDraw.Draw(collage)
    date_dimension = template_draw.textsize(collage_date, img_font)

    text_x = collage_section_width * 3 / 2 - date_dimension[0] / 2
    text_y = collage_section_height - date_dimension[1] * 0.1

    template_draw.text(xy=(text_x, text_y), text=collage_date, fill=font_color, font=img_font)

    inmemory_file = put_image_in_memory(collage, 'starting-%s' % str(uuid4().hex))

    thumbnail = collage.resize((600, 600), Image.ANTIALIAS)

    thumbnail_inmemory_file = put_image_in_memory(thumbnail, 'tn_starting-%s' % str(uuid4().hex))

    result = save_image(
        user=checkpoint_photo.user,
        date=checkpoint_photo.date,
        image_type='CHECKPOINT_PHOTO',
        image_file=inmemory_file,
        thumbnail_file=thumbnail_inmemory_file,
        is_published=True
    )

    return [result]


def save_image(user, date, image_type, image_file, thumbnail_file, is_published=True, remove_existing=True):
    """ Сохраняет изображение SRBCImage. При этои удаляет текущее изображение, если имеется.

    :param user:
    :type user: django.contrib.auth.models.User
    :param date:
    :type date: datetime.date
    :param image_type: смотри `srbc.models.SRBCImage.image_type`
    :type image_type: str
    :param image: image object
    :param image_file: file like object
    :param thumbnail_file: file like object
    :param is_published: boolean flag (default - True) whether new image should be immidiately published to the stream
    :param remove_existing: Если True, то удаляет фото за `date`
    :type remove_existing: bool
    :return: SRBCImage object or None (in case of error)
    :rtype: srbc.models.SRBCImage | None
    """

    if remove_existing:
        existing_image = SRBCImage.objects.filter(user=user, date=date, image_type=image_type).first()

        if existing_image:
            # очищаем
            if not existing_image.is_editable:
                return None

            if existing_image.thumbnail:
                existing_image.thumbnail.delete(save=False)

            if existing_image.image:
                existing_image.image.delete(save=False)

            image_to_save = existing_image
        else:
            image_to_save = SRBCImage(user=user, date=date, image_type=image_type)
    else:
        image_to_save = SRBCImage(user=user, date=date, image_type=image_type)

    image_to_save.thumbnail = thumbnail_file
    image_to_save.image = image_file
    image_to_save.date_added = timezone.now()
    image_to_save.is_published = is_published

    image_to_save.save()

    return image_to_save


def square_crop(image):
    """ Кропает изображение до квадрата.
    NB: изменяет объект image.

    :param image: image instance
    :type image: PIL.Image.Image
    """
    w, h = image.size
    longer_side = max(w, h)
    horizontal_padding = (longer_side - w) / 2
    vertical_padding = (longer_side - h) / 2

    return image.crop((-horizontal_padding, -vertical_padding, w + horizontal_padding, h + vertical_padding))


def put_image_in_memory(image, filename):
    """ Сохраняет и помещает изображение в InMemoryUploadedFile

    :param image:
    :type image: PIL.Image.Image
    :param filename:
    :type filename: str
    :return: загруженный в память файл
    :rtype: django.core.files.uploadedfile.InMemoryUploadedFile
    """
    io_buffer = io.BytesIO()

    # сохраним таблицу квантования до convert-а (есть только у JPEG)
    jpeg_qtable = getattr(image, 'quantization', None)

    if image.mode != 'RGB':
        # переводим изображение в RGB для того, чтобы можно было спокойно сохранить в JPEG
        image = image.convert('RGB')

    # Сохраняем в буффер
    # For JPEG:
    # optimize - the encoder should make an extra pass over the image in order to select optimal encoder settings.
    # progressive - this image should be stored as a progressive JPEG file.
    if jpeg_qtable:
        # сохраним изображение с таблицей квантования оригинала для того,
        # чтобы результирующее изображение не было больше оригинала (в байтах)
        # (грубо говоря, решает проблему того, что при сохранении изображения с quality=90
        #  результирующее изображение может быть больше оригинала, если quality оригинала!=90)
        image.save(io_buffer, 'JPEG', optimize=True, progressive=True, qtable=jpeg_qtable)
    else:
        image.save(io_buffer, 'JPEG', quality=90, optimize=True, progressive=True)

    in_memory_file = InMemoryUploadedFile(file=io_buffer, field_name=None,
                                          name='%s.%s' % (filename, 'jpeg'), content_type='image/jpeg',
                                          size=io_buffer.getbuffer().nbytes, charset=None, content_type_extra=None)

    return in_memory_file


def save_srbc_image(user, image_date, image_data, image_type, remove_existing=True, is_published=False, as_is=False):
    """ Проверяет корректность изображения для рациона дневника и сохраняет его.

    :param user:
    :type user: django.contrib.auth.models.User
    :param image_date:
    :type image_date: str
    :param image_data: base64 image data
    :type image_data: str
    :param image_type: смотри `srbc.models.SRBCImage.image_type`
    :type image_type: str
    :param remove_existing:
    :type remove_existing: bool
    :param is_published:
    :type is_published: bool
    :param as_is: save image AS_IS (if False - crops to square)
    :type as_is: bool
    :return: SRBCImage or None (in case of error)
    :rtype: srbc.models.SRBCImage | None
    """

    tz = pytz.timezone(user.profile.timezone)
    image_date = tz.localize(datetime.datetime.strptime(image_date, "%Y-%m-%d"))

    img_format, img_str = image_data.split(';base64,')

    # 1) базовые проверки
    if '/' not in img_format or not img_str:
        # ожидали img_format вида "data:image/png", img_str вида "iVBORw0...", но получили что-то другое
        logger.error('[save_srbc_image] Wrong image_data', extra={'img_format': img_format, 'img_str': img_str})
        return None

    ext = img_format.split('/')[-1]
    filename = str(uuid4())
    file_data = ContentFile(base64.b64decode(img_str), name='%s.%s' % (filename, ext))

    with Image.open(file_data) as image:
        w, h = image.size

        # 2) Если отличие между шириной и высотой более 1% - не принимаем фото
        percent_diff = abs(w - h) / ((w + h) / 2) * 100
        percent_diff = round(abs(percent_diff))
        if percent_diff > 1:
            return None

        filename = str(uuid4())

        if not as_is:
            # === сохраняем изображение с кропом до квадрата
            # 3) Кропаем до квадрата
            if w != h:
                image = square_crop(image)

            # 4) Ресайзим изображение
            # Для больших изображений создаем 2 изображения (600х600, 1200х1200), для маленьких - одно (600х600)).

            # создаем изображение (1200х1200)
            if w > 1200:
                image = image.resize((1200, 1200), Image.ANTIALIAS)

            image_file = put_image_in_memory(image=image, filename=filename)

            if w > 600:
                thumbnail = image.resize((600, 600), Image.ANTIALIAS)
            else:
                thumbnail = image.copy()

            thumbnail_file = put_image_in_memory(image=thumbnail, filename="tn_%s" % filename)
        else:
            # === сохраняем изображение как есть
            image_file = put_image_in_memory(image=image, filename=filename)
            thumbnail = image.resize((w / 2, h / 2), Image.ANTIALIAS)
            thumbnail_file = put_image_in_memory(image=thumbnail, filename="tn_%s" % filename)

    return save_image(
        user=user,
        date=image_date,
        image_type=image_type,
        image_file=image_file,
        thumbnail_file=thumbnail_file,
        is_published=is_published,
        remove_existing=remove_existing
    )


def exist_images_to_collage(diary):
    # Проверяем есть ли изображения для сборки коллажа
    qs = DiaryMeal.objects.filter(diary=diary).order_by('start_time_is_next_day', 'start_time').only('meal_image')
    for diary_meal in qs:
        if not diary_meal.meal_image:
            continue

        else:
            return True

    return False


def create_meal_collage(diary):
    """ Создает коллаж рациона для дневника питания

    :param diary:
    :type diary: srbc.models.DiaryRecord
    :return: SRBCImage object or None
    :rtype: srbc.models.SRBCImage | None
    """
    images = []
    qs = DiaryMeal.objects.filter(
        diary=diary).order_by(
        'start_time_is_next_day', 'start_time').only(
        'meal_image', 'meal_image_status')
    for diary_meal in qs:
        if not diary_meal.meal_image:
            continue

        if diary_meal.meal_image_status in [DiaryMeal.IMAGE_STATUS_FAKE_DATE, DiaryMeal.IMAGE_STATUS_FAKE_NO_DATE]:
            file_to_read = draw_fake_mark(diary_meal.meal_image)
            pil_img = Image.open(file_to_read)
        else:
            img_raw = diary_meal.meal_image.read()
            pil_img = Image.open(ContentFile(img_raw))

        images.append(pil_img)

    return save_meal_collage(user=diary.user, images=images, date=diary.date, yesterday_date=True)


def save_meal_collage(user, images, date, yesterday_date=False):
    """ Формирует и сохраняет коллаж рациона.

    :param user:
    :type user: django.contrib.auth.models.User
    :param images: list of images
    :type images: list
    :param date:
    :type date: datetime.date
    :param yesterday_date: если True, то подпись к коллажу будет сформирована за вчерашнуюю дата (param date)
    :type yesterday_date: bool
    :return: SRBCImage object or None
    :rtype: srbc.models.SRBCImage | None
    """
    if not images:
        return None

    collage_width = 1200
    full_collage_height = 1200
    images_collage_height = int(full_collage_height * 0.9)  # 90% высоту используем под коллжал, 10% - под надпись даты

    images_count = len(images)

    n = 1
    while True:
        if pow(n + 1, 2) >= images_count:
            break
        else:
            n += 1

    rows_count = n if images_count < (n * (n + 1)) else (n + 1)
    print(('\tCollage: %d rows' % rows_count))

    imgs_in_rows = [0] * rows_count
    for i in range(images_count):
        _col = (i % rows_count) + 1
        imgs_in_rows[-_col] += 1

    print(('\tCollage images per row: %s' % imgs_in_rows))

    collage_img = Image.new('RGB', (collage_width, full_collage_height))

    shift = 0
    height = images_collage_height // rows_count
    row_n = 0
    for imgs_amount in imgs_in_rows:
        new_shift = shift + imgs_amount

        width = 1200 // imgs_amount
        row_images = images[shift:new_shift]
        for col_n, img in enumerate(row_images):
            img = ResizeToFill(width, height).process(img)
            # img = Crop(width-2, height-2, Anchor.CENTER).process(img)
            img = AddBorder(thickness=1, color=(153, 158, 255, 0)).process(img)
            collage_img.paste(img, (col_n * width, row_n * height))

        shift = new_shift
        row_n += 1

    # === DRAW text
    path_to_assets = os.path.join(settings.BASE_DIR, "srbc", "assets", "collage_data")
    path_to_font = os.path.join(path_to_assets, "days.ttf")
    img_font = ImageFont.truetype(path_to_font, 90)
    font_color = (255, 255, 255)

    template_draw = ImageDraw.Draw(collage_img)

    if yesterday_date:
        collage_date = (date - datetime.timedelta(days=1)).__format__("%d.%m.%Y")
    else:
        collage_date = date.__format__("%d.%m.%Y")
    date_dimension = template_draw.textsize(collage_date, img_font)

    text_x = (collage_width - date_dimension[0]) / 2
    text_y = full_collage_height - date_dimension[1] - 25  # 25 - for padding

    template_draw.text(xy=(text_x, text_y), text=collage_date, fill=font_color, font=img_font)

    # === Save collage
    filename = str(uuid4())
    image_file = put_image_in_memory(image=collage_img, filename=filename)
    thumbnail_file = put_image_in_memory(
        image=collage_img.resize((600, 600), Image.ANTIALIAS), filename="tn_%s" % filename
    )

    return save_image(
        user=user,
        date=date,
        image_type='MEAL',
        image_file=image_file,
        thumbnail_file=thumbnail_file,
        is_published=True,
        remove_existing=True
    )


def draw_fake_mark(image_file):
    """ Draws a fake mark on image.

    :param image_file:
    :type image_file: django.core.files.uploadedfile.InMemoryUploadedFile
    :rtype: django.core.files.uploadedfile.InMemoryUploadedFile
    """
    im = Image.open(image_file)

    draw = ImageDraw.Draw(im)
    draw.line((im.width, 0, 0, im.height), fill=(252, 209, 42), width=20)
    del draw

    return put_image_in_memory(im, image_file.name)


def clean_exif_data(image_exif):
    exif_tags_to_save = [
        'DateTime', 'DateTimeDigitized', 'DateTimeOriginal', 'PreviewDateTime', 'LensMake', 'LensModel', 'Make',
        'Model', 'GPSInfo', 'Orientation'
    ]

    exif_data = {
        k: str("%s" % v).replace('\0', '')
        for k, v in image_exif.items() if k in exif_tags_to_save
    }

    gps_tags = image_exif.get('GPSInfo', {})
    if isinstance(gps_tags, dict):
        exif_data['GPSInfo'] = {ExifTags.GPSTAGS[k]: str("%s" % v).replace('\0', '') for k, v in
                                gps_tags.items() if k in ExifTags.GPSTAGS}
    else:
        gps_tags = '%s' % gps_tags
        exif_data['GPSInfo'] = gps_tags.replace('\0', '')

    logger.info("EXIF data: %s" % exif_data)

    return exif_data


def get_meal_components_text(meal):
    others_types = [
        MealProduct.TYPE_FATCARB,
        MealProduct.TYPE_DEADWEIGHT,
        MealProduct.TYPE_DFRUIT,
        MealProduct.TYPE_DESERT,
        MealProduct.TYPE_ALCO,
        MealProduct.TYPE_UFS,
        MealProduct.TYPE_MIX
    ]

    group_by_types = {
        MealProduct.TYPE_PROTEIN : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_FAT : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_BREAD : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_RAWCARB : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_CARB : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_FRUIT: {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_CARBVEG : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_VEG : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_DESERT : {
            'products' : [],
            'weight' : 0
        },
        

        MealProduct.TYPE_DEADWEIGHT : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_UNKNOWN : {
            'products' : [],
            'weight' : 0
        },
        MealProduct.TYPE_DRINK : {
            'products' : [],
            'weight' : 0
        },
        'OTHERS' : {
            'products' : [],
            'weight' : 0
        },

    }

    qs = MealComponent.objects.filter(meal=meal).only('description', 'weight')
    for c in qs:
        if c.component_type in others_types:
            group_by_types['OTHERS']['weight'] += c.weight
            group_by_types['OTHERS']['products'].append(c.description)
        else:
            group_by_types[c.component_type]['weight'] += c.weight
            group_by_types[c.component_type]['products'].append(c.description)

    components_text = ""
    for k,v in group_by_types.items():
        if v['weight'] != 0:
            components_text += "%s%g %s" % (', ' if components_text != "" else '', v['weight'], v['products'])
            components_text = components_text.replace("'", "")
    return components_text
