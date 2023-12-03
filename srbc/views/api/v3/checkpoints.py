from PIL import Image, ExifTags
from uuid import uuid4
import hashlib
import logging
import base64
import io
import pytz
from datetime import datetime

from rest_framework.views import APIView
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework import status
from rest_framework.response import Response
from django.core.files.uploadedfile import InMemoryUploadedFile
from srbc.utils.permissions import IsActiveUser, IsWaveUser
from rest_framework.permissions import IsAuthenticated, AllowAny
from srbc.models import CheckpointPhotos
from django.core.files.base import ContentFile
from srbc.utils.srbc_image import put_image_in_memory
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs


logger = logging.getLogger('USER_PHOTO_UPLOAD_API')

class UserPhotoUploadAPIView(LoggingMixin, APIView):

    permission_classes = (IsAuthenticated, )

    @staticmethod
    def get_image(user, image_data):
        """ Проверят и сохраняет изображение в памяти.

        :param user:
        :type user: django.contrib.auth.models.User
        :param image_data: base64 image data
        :type image_data: str
        :return: image and exif
        :rtype: (django.core.files.uploadedfile.InMemoryUploadedFile, dict) | (None, dict)
        """
        img_format, img_str = image_data.split(';base64,')

        # 1) базовые проверки
        if '/' not in img_format or not img_str:
            # ожидали img_format вида "data:image/png", img_str вида "iVBORw0...", но получили что-то другое
            logger.error('[user_photo_upload] Wrong image_data',
                         extra={'img_format': img_format, 'img_str': img_str})
            return None

        ext = img_format.split('/')[-1]
        filename = str(uuid4())
        file_data = ContentFile(base64.b64decode(img_str), name='%s.%s' % (filename, ext))

        return file_data
        

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['POST /v3/checkpoints/photos/']
    )
    def post(request):
        checkpoint_date = None

        min_width = 800
        min_height = 1200

        hashes = []

        types = ['face', 'side', 'rear']

        photos = {}

        for name in types:
            image_data = request.data.get(name,None)
            if not image_data:
                return Response(
                        data={
                            "code": status.HTTP_400_BAD_REQUEST,
                            "status": "error",
                            "message": "Необходимо загрузить три фотографии",
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            file_data = UserPhotoUploadAPIView.get_image(request.user,image_data.get('image'))
            with Image.open(file_data) as img_obj:
                exif = image_data.get('exif')
                if not img_obj:
                    return Response(
                        data={
                            "code": status.HTTP_400_BAD_REQUEST,
                            "status": "error",
                            "message": "Необходимо загрузить три фотографии: анфас, в профиль и со спины",
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                tags_to_parse = [
                    'DateTime', 'DateTimeOriginal', 'Orientation',
                ]

                exif_tags =  {
                    k: str("%s" % v).replace('\0', '')
                    for k, v in exif.items() if k in tags_to_parse
                }

                photo_date = exif_tags.get('DateTime') or exif_tags.get('DateTimeOriginal')

                if photo_date is None:
                    return Response(
                        data={
                            "code": status.HTTP_400_BAD_REQUEST,
                            "status": "error",
                            "message": "Необходимо загрузить неотредактированные исходники фотографий",
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    photo_date = photo_date[:10]

                if not checkpoint_date:
                    checkpoint_date = photo_date
                else:
                    if checkpoint_date != photo_date:
                        return Response(
                            data={
                                "code": status.HTTP_400_BAD_REQUEST,
                                "status": "error",
                                "message": "Все три фотографии должны быть сделаны в один день",
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )   

                orientation = exif_tags.get('Orientation')

                if orientation:
                    if orientation == 3:
                        img_obj = img_obj.rotate(180, expand=True)
                    elif orientation == 6:
                        img_obj = img_obj.rotate(270, expand=True)
                    elif orientation == 8:
                        img_obj = img_obj.rotate(90, expand=True)

                width, height = img_obj.size

                if width < min_width or height < min_height:
                    return Response(
                            data={
                                "code": status.HTTP_400_BAD_REQUEST,
                                "status": "error",
                                "message": "Размер каждой фотографии (ШхВ) должен быть не менее чем 800x1200",
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                hashes.append(
                    hashlib.md5(img_obj.tobytes()).hexdigest()
                )

                file_io = io.BytesIO()
                img_obj.save(file_io, format='JPEG', quality=95)

                img_file = InMemoryUploadedFile(
                    file_io, None, '%s.jpg' % name, 'image/jpeg',
                    file_io.getbuffer().nbytes, None
                )

                photos[name] = img_file

        tz = pytz.timezone(request.user.profile.timezone)
        checkpoint_date = checkpoint_date.replace('-', ':')
        checkpoint_date = tz.localize(datetime.strptime(checkpoint_date, "%Y:%m:%d")).date()

        checkpoint = CheckpointPhotos.objects.filter(user=request.user, date=checkpoint_date).first()
        if checkpoint:
            if checkpoint.status == 'APPROVED':
                return Response(
                        data={
                            "code": status.HTTP_400_BAD_REQUEST,
                            "status": "error",
                            "message": "Фотографии за эту дату уже загружены и проверены",
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            checkpoint = CheckpointPhotos(user=request.user, date=checkpoint_date)

        if len(list(set(hashes))) != 3:
            return Response(
                        data={
                            "code": status.HTTP_400_BAD_REQUEST,
                            "status": "error",
                            "message": "Нужны три РАЗНЫХ фотографии – с трёх ракурсов",
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

        checkpoints_exists = CheckpointPhotos.objects.filter(status='APPROVED', user=request.user).exists()

        checkpoint.front_image = photos.get('face')
        checkpoint.side_image = photos.get('side')
        checkpoint.rear_image = photos.get('rear')
        checkpoint.status = 'APPROVED' if checkpoints_exists else 'NEW'

        checkpoint.save()
        return Response(
                        f"Контрольные фотографии за {checkpoint_date} успешно загружены",
                        status=status.HTTP_200_OK
                    )