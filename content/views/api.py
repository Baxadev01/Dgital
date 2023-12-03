# -*- coding: utf-8 -*-
import logging
import os
import mimetypes
from wsgiref.util import FileWrapper

from django.shortcuts import redirect
from django.http import StreamingHttpResponse
from django.http.response import Http404
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.http.response import Http404
from django.utils import timezone
from django_telegrambot.apps import DjangoTelegramBot
from django_telegrambot.views import BadRequest
from markdownx.utils import markdownify
from rest_framework import status, viewsets, generics
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.decorators import login_required, user_passes_test
from srbc.decorators import validate_user, has_desktop_access
from content.models import Meeting, MeetingPlayHistory
from content.views.meetings import check_meeting_referer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny 
from django.utils.decorators import method_decorator
from django.db.models import Q


from srbc.utils.permissions import IsActiveUser, IsWaveUser
from content.models import Article, TGChat, TGChatParticipant, TGMessage, TGPost, Recipe
from content.serializers import (ArticleSerializer, ArticlesSerializer, MeetingSerializer, TGChatSerializer,
                                 TGMessageSerializer, TGPostSerializer, RecipesSerializer)

from content.utils import store_dialogue_reply, get_user_meetings, messsage_reject_notification, \
    message_respond_with_post, notify_about_post


from swagger_docs import swagger_docs
from srbc.serializers.general import UserProfileSerializer
from srbc.utils.permissions import IsActiveUser, IsValidUser, HasExpertiseAccess, HasMeetingAccess, \
    JSONWebTokenMobileAuthentication
from srbc.models import Tariff, TariffGroup


logger = logging.getLogger(__name__)


class TgUsersViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsAdminUser,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/tg/users/']
    )
    def list(request):
        """
            Получение пользователей из телеграм канала
        """
        channel = TGChat.objects.filter(pk=request.GET.get('channel_id')).first()
        result = []
        if channel:
            serializer = UserProfileSerializer(channel.members, many=True)
            result = serializer.data

        return Response(result)


class MeetingsViewSet(LoggingMixin, viewsets.ViewSet):
    authentication_classes = [JSONWebTokenMobileAuthentication, ]
    permission_classes = (IsAuthenticated, IsActiveUser, HasMeetingAccess,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/content/meetings/']
    )
    def list(request):
        """
            Выводит список лекций
        """
        meetings = get_user_meetings(request.user)

        serializer = MeetingSerializer(meetings, many=True)
        result = serializer.data

        return Response(result)


class UsersChatSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsValidUser, HasExpertiseAccess, )

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['HEAD /v1/chat/{chat_id}/notify/']
    )
    def notify_user(request, chat_id):
        """
            Уведомление пользователя для присоединения к чату
        """
        chat_to_join = TGChatParticipant.objects.filter(user=request.user, status__in=['ALLOWED', 'LEFT'],
                                                        chat_id=chat_id).first()

        if chat_to_join:
            chat_to_join = chat_to_join.chat

            post_notification = "Для присоединения к %s %s [%s], жми на ссылку: https://t.me/joinchat/%s" % (
                "чату" if chat_to_join.chat_type == 'CHAT' else "каналу",
                chat_to_join.title,
                chat_to_join.code,
                chat_to_join.tg_slug,
            )

            msg = DjangoTelegramBot.dispatcher.bot.send_message(
                chat_id=request.user.profile.telegram_id,
                text=post_notification,
                disable_web_page_preview=True
            )
            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

            result = "ok"
        else:
            result = 'not_found'

        return Response({"result": result})


class TgMessagesViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsAdminUser,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/tg/messages/']
    )
    def list(request):
        """
            Получение списка сообщений в телеграме
        """
        channel = TGChat.objects.filter(pk=request.GET.get('channel_id')).first()

        queryset = TGMessage.objects.filter(author__chats=channel)

        if 'author_id' in request.GET:
            queryset = queryset.filter(author_id=request.GET.get('author_id'))

        if 'message_type' in request.GET:
            queryset = queryset.filter(message_type=request.GET.get('message_type'))

        if 'status' in request.GET:
            queryset = queryset.filter(status=request.GET.get('status'))

            if request.GET.get('status') == 'NEW':
                queryset = queryset.order_by('created_at')
            else:
                queryset = queryset.order_by('-resolved_at')
        else:
            queryset = queryset.order_by('-created_at')

        if 'answer_id' in request.GET:
            queryset = queryset.filter(answer_id=request.GET.get('answer_id'))

        queryset = queryset.all()[:100]

        serializer = TGMessageSerializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/tg/messages/{message_id}/']
    )
    def update_one(request, message_id):
        """
            Редактировать сообщения из телеграма
        """
        message_data = request.data
        new_status = message_data.get('status')
        new_type = message_data.get('message_type')
        try:
            tg_message = TGMessage.objects.get(pk=message_id)
        except ObjectDoesNotExist:
            return Response(
                {
                    "error": "Сообщение это найти не могу я",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if new_status:
            if new_status == 'REJECTED':
                messsage_reject_notification(tg_message, request.user)
            else:
                tg_message.status = new_status
                tg_message.resolved_at = timezone.localtime(timezone=timezone.utc)
                tg_message.resolved_by = request.user
                tg_message.save()

        if new_type:
            tg_message.message_type = new_type
            tg_message.save(update_fields=['message_type'])

        serializer = TGMessageSerializer(tg_message)

        return Response(serializer.data)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/tg/messages/{message_id}/']
    )
    def get_one(request, message_id):
        """
            Получение сообщения из телеграма
        """
        try:
            tg_message = TGMessage.objects.get(pk=message_id)
        except ObjectDoesNotExist:
            return Response({
                "error": "Сообщение это найти не могу никому я"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TGMessageSerializer(tg_message)

        return Response(serializer.data)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/tg/messages/']
    )
    def respond(request):
        """
            Опубликовать пост
        """
        post_id = request.data.get('post_id')

        existing_post = TGPost.objects.filter(pk=post_id).first()

        if not existing_post:
            return Response({
                "error": "Ответить несуществующим сообщением не могу я"
            }, status=status.HTTP_400_BAD_REQUEST)

        channel_id = existing_post.channel_id or request.data.get('channel_id')
        channel = TGChat.objects.filter(pk=channel_id).first()

        if not channel:
            return Response({
                "error": "Непонимаю, куда отправлять сообщение"
            }, status=status.HTTP_400_BAD_REQUEST)

        additional_recipients = request.data.get('additional_recipients', [])
        additional_recipients = list(set(additional_recipients))
        users_not_found = []
        users_found = []
        for recipient in additional_recipients:
            _target = User.objects.filter(
                profile__telegram_id__isnull=False,
                chats=channel
            )

            if recipient.strip()[:3] == '@tg':
                _target = _target.filter(
                    profile__telegram_id=recipient.strip()[3:]
                )
            elif recipient.strip()[:5] == '@srbc':
                _target = _target.filter(
                    pk=recipient.strip()[5:]
                )
            else:
                _target = _target.filter(
                    username=recipient.strip(),
                )

            _target = _target.first()
            if _target:
                users_found.append(_target)
            else:
                users_not_found.append(recipient.strip())

        if len(users_not_found):
            return Response({
                "error": "Вот этих пользователей я не нашёл: %s" % ", ".join(users_not_found)
            }, status=status.HTTP_400_BAD_REQUEST)

        if not existing_post.is_private and not existing_post.is_posted:
            return Response({
                "error": "Опубликовать это сообщение в канале сперва должен ты",
            }, status=status.HTTP_400_BAD_REQUEST)

        respond_to_ids = request.data.get('respond_to', [])

        messages_to_respond = TGMessage.objects.filter(pk__in=respond_to_ids)
        for tg_message in messages_to_respond:
            try:
                message_respond_with_post(message=tg_message, post=existing_post, responded_by=request.user)
            except BadRequest as e:
                return Response(
                    {
                        "error": "Ошибка отправки сообщения: %s" % e.message
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        for recipient in users_found:
            try:
                notify_about_post(post=existing_post, recipient=recipient, responded_by=request.user)
            except BadRequest as e:
                return Response(
                    {
                        "error": "Ошибка отправки сообщения: %s" % e.message
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = TGMessageSerializer(messages_to_respond, many=True)

        return Response(serializer.data)


class TgChannelsViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsAdminUser,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/tg/channels/']
    )
    def list(request):
        """
            Получение списка каналов в телеграме
        """
        queryset = TGChat.objects.filter(is_active=True).prefetch_related(
            Prefetch('members', queryset=User.objects.select_related('profile'))
        ).order_by('start_date').prefetch_related()
        serializer = TGChatSerializer(queryset, many=True)
        return Response(serializer.data)


class TgPostsViewSet(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsAdminUser,)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/tg/posts/']
    )
    def list(request):
        """
            Получение списка постов из телеграма
        """
        queryset = TGPost.objects.order_by('-created_at')
        if 'search' in request.GET:
            words = request.GET.get('search').split(" ")
            for word in words:
                if len(word):
                    queryset = queryset.filter(text__icontains=word)
        if 'private' in request.GET:
            queryset = queryset.filter(is_private=True)
        else:
            queryset = queryset.filter(is_private=False)

        if 'channel_id' in request.GET:
            queryset = queryset.filter(channel_id=request.GET.get('channel_id'))

        if 'author_id' in request.GET:
            queryset = queryset.filter(author_id=request.GET.get('author_id'))

        if 'is_private' in request.GET:
            queryset = queryset.filter(is_private=request.GET.get('is_private'))

        queryset = queryset.all()[:20]
        queryset = list(queryset)
        serializer = TGPostSerializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/tg/posts/{post_id}/']
    )
    def get_one(request, post_id):
        """
            Получение поста из телеграма
        """
        try:
            new_post = TGPost.objects.get(pk=post_id)
        except ObjectDoesNotExist:
            return Response({
                "error": "Сообщение это найти не могу никому я"
            }, status=status.HTTP_404_NOT_FOUND)

        post_serializer = TGPostSerializer(new_post)

        return Response(post_serializer.data)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['PUT /v1/tg/posts/{post_id}/']
    )
    def update_one(request, post_id):
        """
            Редактировать пост из телеграма
        """
        post_data = request.data
        post_text = post_data.get('text', '').strip()
        if len(post_text):
            try:
                new_post = TGPost.objects.get(pk=post_id)
            except ObjectDoesNotExist:
                return Response({
                    "error": "Сообщение это найти не могу никому я"
                }, status=status.HTTP_404_NOT_FOUND)

            new_post.text = post_text
            new_post.save()
            post_serializer = TGPostSerializer(new_post)

            if not new_post.is_private and new_post.is_posted and new_post.message_id:

                wave_slug = new_post.channel.code.replace(".", "")
                if new_post.image_url:
                    channel_post_text = "%s\n(#srbc_%s%05d)" % (new_post.text, wave_slug, new_post.pk)
                    DjangoTelegramBot.dispatcher.bot.edit_message_caption(
                        chat_id=new_post.channel.tg_id,
                        caption=channel_post_text,
                        message_id=new_post.message_id,
                    )
                else:
                    wave_slug = new_post.channel.code.replace(".", "")
                    channel_post_text = "%s\n(#srbc\_%s%05d)" % (new_post.text, wave_slug, new_post.pk)
                    DjangoTelegramBot.dispatcher.bot.edit_message_text(
                        chat_id=new_post.channel.tg_id,
                        text=channel_post_text,
                        message_id=new_post.message_id,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )

            return Response(post_serializer.data)

        else:
            return Response({
                "error": "Пустое сообщение отправить не могу никому я"
            }, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['POST /v1/tg/posts/']
    )
    def add(request):
        """
            Создание поста в телеграм
        """
        post_data = request.data.get('post', {})
        post_text = post_data.get('text', '').strip()

        if len(post_text):
            additional_recipients = post_data.get('additional_recipients', [])
            additional_recipients = list(set(additional_recipients))
            users_not_found = []
            users_found = []
            for recipient in additional_recipients:
                channel = TGChat.objects.get(pk=post_data.get('channel_id'))

                _target = User.objects.filter(
                    profile__telegram_id__isnull=False,
                    chats=channel
                )

                if recipient.strip()[:3] == '@tg':
                    _target = _target.filter(
                        profile__telegram_id=recipient.strip()[3:]
                    )
                elif recipient.strip()[:5] == '@srbc':
                    _target = _target.filter(
                        pk=recipient.strip()[5:]
                    )
                else:
                    _target = _target.filter(
                        username=recipient.strip(),
                    )

                _target = _target.first()

                if _target:
                    users_found.append(_target)
                else:
                    users_not_found.append(recipient.strip())

            if len(users_not_found):
                return Response({
                    "error": "Вот этих пользователей я не нашёл: %s" % ", ".join(users_not_found)
                }, status=status.HTTP_400_BAD_REQUEST)

            post_data['is_sticker'] = post_text[:8] == 'STICKER|'

            stickers = {
                'MEETING': {
                    'id': 'CAADAgADIQADT8JICLPteljOfS9YAg',
                    'text': 'Слушай митинг'
                }
            }

            if post_data.get('is_sticker'):
                sticker_slug = post_text[8:]
                sticker_data = stickers.get(sticker_slug)
                if sticker_data:
                    post_data['sticker_data'] = sticker_data
                else:
                    return Response(
                        {
                            "error": "Этот стикер какой-то неселфрербуткэмповый. Или вообще не стикер."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            new_post = TGPost(author=request.user, created_at=timezone.localtime(timezone=timezone.utc), text=post_text)
            new_post.is_private = post_data.get('is_private', False)
            new_post.save()
            post_serializer = TGPostSerializer(new_post)

            if not new_post.is_private:
                channel = TGChat.objects.get(pk=post_data.get('channel_id'))
                channel_slug = channel.code.replace(".", "")
                if post_data.get('image_url'):
                    channel_post_text = "%s\n(#srbc_%s%05d)" % (new_post.text, channel_slug, new_post.pk)
                    try:
                        sent_message = DjangoTelegramBot.dispatcher.bot.send_photo(
                            chat_id=channel.tg_id,
                            photo=post_data.get('image_url'),
                            caption=channel_post_text
                        )
                    except BadRequest as e:
                        return Response(
                            {
                                "error": "Ошибка отправки сообщения: %s" % e.message
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    new_post.image_url = post_data.get('image_url')
                elif post_data.get('sticker_data'):
                    try:
                        sent_message = DjangoTelegramBot.dispatcher.bot.send_sticker(
                            chat_id=channel.tg_id,
                            sticker=post_data.get('sticker_data').get('id')
                        )
                    except BadRequest as e:
                        return Response(
                            {
                                "error": "Ошибка отправки сообщения: %s" % e.message
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                else:
                    channel_post_text = "%s\n(#srbc\_%s%05d)" % (new_post.text, channel_slug, new_post.pk)
                    try:
                        sent_message = DjangoTelegramBot.dispatcher.bot.send_message(
                            chat_id=channel.tg_id,
                            text=channel_post_text,
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                    except BadRequest as e:
                        return Response(
                            {
                                "error": "Ошибка отправки сообщения: %s" % e.message
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # store_dialogue_reply(
                #     message=sent_message.text,
                #     message_id=sent_message.message_id,
                #     tg_user_id=sent_message.chat_id
                # )

                # logger.info(sent_message)

                new_post.channel = channel
                new_post.message_id = sent_message.message_id
                new_post.is_posted = True
                new_post.posted_at = timezone.localtime(timezone=timezone.utc)
                new_post.save()
        else:
            return Response({
                "error": "Пустое сообщение отправить не могу никому я"
            }, status=status.HTTP_400_BAD_REQUEST)

        respond_to_ids = request.data.get('respond_to', [])

        messages_to_respond = TGMessage.objects.filter(pk__in=respond_to_ids)
        for tg_message in messages_to_respond:
            try:
                message_respond_with_post(message=tg_message, post=new_post, responded_by=request.user)
            except BadRequest as e:
                return Response(
                    {
                        "error": "Ошибка отправки сообщения: %s" % e.message
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        for recipient in users_found:
            try:
                notify_about_post(post=new_post, recipient=recipient, responded_by=request.user)
            except BadRequest as e:
                return Response(
                    {
                        "error": "Ошибка отправки сообщения: %s" % e.message
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        messages_serializer = TGMessageSerializer(messages_to_respond, many=True)

        return Response({
            "post": post_serializer.data,
            "messages": messages_serializer.data,
        })


class ArticleSet(LoggingMixin, viewsets.ViewSet):

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/content/articles/']
    )
    def get_articles(request):
        """ Выводит список заголовков статей, доступных пользователю.

        Коды ответов:
        200 - Данные статей

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        :rtype: rest_framework.response.Response
        """
        qs = Article.get_query_by_permission(user=request.user)
        articles = qs.only('id', 'title').order_by('is_published', 'sort_num').all()

        serialized = ArticlesSerializer(instance=articles, many=True)
        return Response(serialized.data)

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/content/articles/{article_id}/']
    )
    def get_article(request, article_id):
        """ Выводит фото, видео, текст статьи, если эта статья доступна пользователю.

        Коды ответов:
        200 - Данные статьи
        404 - Запрашиваемая статья не найдена или нет доступа к ней

        :param request:
        :type request: django.core.handlers.wsgi.WSGIRequest
        :param article_id: id запрашиваемой статьи
        :type article_id: str(int)
        :rtype: rest_framework.response.Response
        """
        qs = Article.get_query_by_permission(user=request.user)
        try:
            article = qs.filter(id=article_id).get()
        except ObjectDoesNotExist:
            raise Http404()
        else:
            article.text = markdownify(article.text)
            serialized = ArticleSerializer(instance=article)
            return Response(serialized.data)


class RecipePagination(PageNumberPagination):
   
   page_size = 24
   page_size_query_param = 'page_size'
   max_page_size = 1000


@method_decorator(name='get', decorator=swagger_auto_schema(
    filter_inspectors=[RecipePagination],
    **swagger_docs['GET /v3/content/recipes/']
))
class RecipeListAPIView(LoggingMixin, generics.ListAPIView):
    """
        Выводит список рецептов
    """

    serializer_class = RecipesSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = RecipePagination

    def get_queryset(self):
        filter_tags = self.request.GET.get('tags')
        search_by = self.request.GET.get('q', '')
        recipes = Recipe.objects
        if filter_tags:
            tags = filter_tags.split(',')
            recipes = recipes.filter(tags__contains=tags)

        if search_by:
            recipes = recipes.filter(
                Q(title__icontains=search_by)
                | Q(body__icontains=search_by)
                | Q(comment__icontains=search_by)
            )

        queryset = recipes.all()

        return queryset


@swagger_auto_schema(
    method='get',
    **swagger_docs['GET /v3/manual/']
)
@api_view(('GET',))
@permission_classes([AllowAny])
@login_required
@has_desktop_access
@validate_user
@user_passes_test(lambda u: u.profile.agreement_signed_date, login_url='/agreement/', redirect_field_name='next')
def manual_download_api(request):
    """
        Скачивание методички
    """
    path_to_assets = os.path.join(settings.BASE_DIR, "content", "assets", "manual")
    the_file = os.path.join(path_to_assets, "srbc_manual_!!!.pdf")

    filename = os.path.basename(the_file)
    filename = filename.replace('!!!', request.user.username)
    chunk_size = 8192
    response = StreamingHttpResponse(FileWrapper(open(the_file, 'rb'), chunk_size),
                                     content_type=mimetypes.guess_type(the_file)[0])
    response['Content-Length'] = os.path.getsize(the_file)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


@swagger_auto_schema(
    method='get',
    **swagger_docs['GET /v3/meetings/{meeting_id}/chunks/{chunk_id}.ts/']
)
@api_view(('GET',))
@permission_classes([AllowAny])
@login_required
@has_desktop_access
@validate_user
def meeting_chunk_api(request, meeting_id, chunk_id):
    
    """
        Получение чанка лекции
    """
    user = request.user

    if not user.is_staff:
        meeting = Meeting.objects.filter(pk=meeting_id)
    else:
        meeting = get_user_meetings(user).filter(pk=meeting_id)

    meeting = meeting.first()

    if not meeting:
        raise Http404()

    referer_check_passed = check_meeting_referer(request=request, meeting_id=meeting_id)

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    mph = MeetingPlayHistory(
        user=request.user,
        meeting=meeting,
        useragent=request.META.get('HTTP_USER_AGENT', ''),
        ip_addr=ip,
        referer_check=referer_check_passed,
        item="chunk.%s" % chunk_id
    )

    mph.save()

    if not referer_check_passed:
        return redirect('/meetings/%s/' % meeting_id)

    filename = os.path.join(settings.MULTIMEDIA_ROOT, 'meetings', meeting_id, 'chunks', "%s.ts" % chunk_id)

    if os.path.isfile(filename):
        mp3content = open(filename, 'rb').read()
        return HttpResponse(mp3content, content_type='audio/mpeg')
    else:
        raise Http404()


@swagger_auto_schema(
    method='get',
    **swagger_docs['GET /v3/meetings/{meeting_id}/playlist.m3u8/']
)
@api_view(('GET',))
@permission_classes([AllowAny])
@login_required
@has_desktop_access
@validate_user
def meeting_playlist_api(request, meeting_id):
    """
        Получение списка чанков для лекции
    """
    user = request.user

    if not user.is_staff:
        meeting = Meeting.objects.filter(pk=meeting_id)
    else:
        meeting = get_user_meetings(user).filter(pk=meeting_id)

    meeting = meeting.first()

    if not meeting:
        raise Http404()

    referer_check_passed = check_meeting_referer(request=request, meeting_id=meeting_id)

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    mph = MeetingPlayHistory(
        user=request.user,
        meeting=meeting,
        useragent=request.META.get('HTTP_USER_AGENT', ''),
        ip_addr=ip,
        referer_check=referer_check_passed
    )

    mph.save()

    if not referer_check_passed:
        return redirect('/meetings/%s/' % meeting_id)

    playlist = open(os.path.join(settings.MULTIMEDIA_ROOT, 'meetings', meeting_id, 'playlist.m3u8'), 'rb').read()
    return HttpResponse(playlist, content_type='application/vnd.apple.mpegurl')