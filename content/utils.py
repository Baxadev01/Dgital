# -*- coding: utf-8 -*-
import logging
from datetime import date

import boto3
import pytz
from botocore.exceptions import ClientError
from django.db.models import F, Sum, Q, Exists, OuterRef, Case, When, IntegerField
from django.db.models.functions import ExtractDay, TruncDate, Least
from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import date as local_strftime
from django.utils import timezone
from django_telegrambot.apps import DjangoTelegramBot

from content.models import Dialogue, Meeting
from srbc.models import TariffGroup
from crm.models import TariffHistory

logger = logging.getLogger(__name__)

s3client = boto3.session.Session().client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    config=boto3.session.Config(
        signature_version=getattr(settings, 'AWS_S3_SIGNATURE_VERSION', None),
        region_name=getattr(settings, 'AWS_S3_REGION_NAME', None),
    )
)


def get_user_meetings(user):
    today = date.today()

    paid_days = TariffHistory.objects.filter(
        user_id=user.pk, is_active=True,
        valid_from__lte=today
    ).exclude(
        tariff__tariff_group__meetings_access=TariffGroup.MEETINGS_NO_ACCESS
    ).aggregate(
        paid_days=Sum(ExtractDay(TruncDate(Least('valid_until', today)) - TruncDate(Least('valid_from', today))) + 1)
    )['paid_days']

    newbie_paid_days = paid_days or 0

    # подквери для проверки существования оплаты в хистори на даты тарифа
    regular_meeting_access_query = TariffHistory.objects.filter(
        user_id=user.pk, valid_from__lte=OuterRef('date'),
        valid_until__gte=OuterRef('date'),
        is_active=True,
        tariff__tariff_group__meetings_access=TariffGroup.MEETINGS_ALL)

    # в выборку должны включить
    # 1 - тарифы для новичков с delay_days меньше чем оплачено у юзера
    # 2 - все регулярные тарифы, вышедшие в период проплаченного времени у юзера за митинговые тарифы
    meetings = Meeting.objects.filter(is_playable=True) \
        .filter(
        Q(type=Meeting.TYPE_NEWBIE, delay_days__lte=newbie_paid_days)
        |
        Q(
            Q(type=Meeting.TYPE_REGULAR)
            &
            Q(Exists(regular_meeting_access_query))
        )
    ).order_by(
        '-type', '-date', '-delay_days', 'order_num'
    )

    return meetings


def store_dialogue_reply(message, message_id, tg_user_id, reply_author=None, user=None):
    if not user:
        user = User.objects.filter(profile__telegram_id=tg_user_id).first()

    dialogue_message = Dialogue(
        tg_user_id=tg_user_id,
        text=message,
        is_incoming=False,
        tg_message_id=message_id,
    )

    if user:
        dialogue_message.user = user

    if reply_author:
        dialogue_message.answered_by = reply_author

    dialogue_message.save()


def _generate_presigned_url(key):
    """ s3client.generate_presigned_url with exception processing

    :type key: basestring
    :rtype: basestring | None
    """
    try:
        link = s3client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': key
            }
        )
    except ClientError as e:
        logger.error(e)
        return None

    return link


def generate_article_video_src(obj):
    """ Если у статьи есть видео, то генерирует ссылки на видео в HD, MD, SD разрешениях

    :param obj: объект статьи
    :type obj: content.models.Article
    :return: {"hd": <link>, "md": <link>, "sd": <link>}
    :rtype: dict
    """
    if obj.has_video:
        return {
            'hd': _generate_presigned_url(key='video/%s/720p.mp4' % obj.id),
            'md': _generate_presigned_url(key='video/%s/480p.mp4' % obj.id),
            'sd': _generate_presigned_url(key='video/%s/360p.mp4' % obj.id),
        }
    else:
        return {}


def generate_meeting_src_link(obj):
    """
    :type obj: content.models.Meeting
    :rtype: basestring | None
    """
    return _generate_presigned_url(key='meetings/{meeting_id}/source/compressed.mp3'.format(meeting_id=obj.id))


def messsage_reject_notification(message, responded_by):
    if message.author.profile.telegram_id:
        response_message = "Ваш вопрос задан с нарушением наших требований к лексике и формулировкам вопросов. " \
                           "Ознакомиться с ними вы можете по ссылке https://lk.selfreboot.camp/articles/lexicon/.\n" \
                           "Пожалуйста, сформулируйте свой вопрос заново в корректной форме и " \
                           "повторно отправьте его боту с тегом #вопрос."

        sent_message = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=message.author.profile.telegram_id,
            reply_to_message_id=message.tg_message_id,
            text=response_message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

        store_dialogue_reply(
            message=sent_message.text,
            message_id=sent_message.message_id,
            tg_user_id=sent_message.chat_id,
            reply_author=responded_by
        )

        # logger.info(sent_message)

    message.status = 'REJECTED'
    message.resolved_at = timezone.localtime(timezone=timezone.utc)
    message.resolved_by = responded_by
    message.answer = None
    message.save()


def message_respond_with_post(message, post, responded_by=None):
    if message.author.profile.telegram_id:
        if post.is_private:
            response_message = post.text
        else:
            message_responded_notification = "На ваш вопрос был дан ответ в информационном канале %s в %s. " \
                                             "Ищите по хэштегу (%s)"
            channel_slug = post.channel.code.replace(".", "")
            post_hashtag = "#srbc\_%s%05d" % (channel_slug, post.pk)
            created_local = timezone.localtime(post.posted_at, timezone=pytz.timezone(message.author.profile.timezone))
            response_date = local_strftime(created_local, 'j E')
            response_time = local_strftime(created_local, 'H:i')
            response_message = message_responded_notification % (response_date, response_time, post_hashtag)

        sent_message = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=message.author.profile.telegram_id,
            reply_to_message_id=message.tg_message_id,
            text=response_message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

        # logger.info(sent_message)
        store_dialogue_reply(
            message=sent_message.text,
            message_id=sent_message.message_id,
            tg_user_id=sent_message.chat_id,
            reply_author=responded_by
        )

    message.status = 'ANSWERED'
    message.resolved_at = timezone.localtime(timezone=timezone.utc)
    message.resolved_by = responded_by
    message.answer = post
    message.save()


def notify_about_post(recipient, post, responded_by=None):
    if post.is_private:
        response_message = post.text
    else:
        post_notification = "Дорогой участник, нам требуется ваша личная реакция на сообщение c хэштегом %s.\n" \
                            "Пожалуйста, внимательно прочитайте его и напишите нам."
        channel_slug = post.channel.code.replace(".", "")
        post_hashtag = "#srbc\_%s%05d" % (channel_slug, post.pk)
        response_message = post_notification % post_hashtag

    sent_message = DjangoTelegramBot.dispatcher.bot.send_message(
        chat_id=recipient.profile.telegram_id,
        text=response_message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    # logger.info(sent_message)
    store_dialogue_reply(
        message=sent_message.text,
        message_id=sent_message.message_id,
        tg_user_id=sent_message.chat_id,
        reply_author=responded_by
    )
