from uuid import uuid4
from datetime import date

from django.db import models
from django.utils.translation import ugettext_lazy as _

from markdownx.models import MarkdownxField

from .utils import picture_upload_to

__all__ = ('Article',)


class Article(models.Model):
    uid = models.UUIDField(max_length=32, unique=True, editable=False, default=uuid4)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=50, unique=True)
    text = MarkdownxField(blank=True, default='')
    sort_num = models.SmallIntegerField(blank=True, default=99)
    is_published = models.BooleanField(blank=True, default=False)
    is_public = models.BooleanField(blank=True, default=False)
    has_video = models.BooleanField(blank=True, default=False, verbose_name="Есть видео")
    main_image = models.ImageField(
        upload_to=picture_upload_to, blank=True, null=True, verbose_name="Заглавное изображение"
    )

    class Meta:
        verbose_name = _('статья')
        verbose_name_plural = _('статьи')

    @classmethod
    def get_query_by_permission(cls, user):
        """ Генерируерт QuerySet на основании доступа юзера к статьям для дальнейшей выборки.

        :param user: объект юзера
        :type user: django.contrib.auth.models.User
        :return: QuerySet с фильтрами под права на доступ юзера к статьям
        :rtype: django.db.models.query.QuerySet
        """
        is_participant = bool(user.is_authenticated
                              and user.profile.valid_until
                              and user.profile.valid_until >= date.today()
                              and user.profile.tariff
                              and user.profile.tariff.tariff_group.kb_access)

        query = cls.objects

        if not user.is_staff:
            query = query.filter(is_published=True)

        if not is_participant:
            query = query.filter(is_public=True)

        return query
