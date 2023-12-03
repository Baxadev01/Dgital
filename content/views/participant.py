# -*- coding: utf-8 -*-
import mimetypes
import os
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import StreamingHttpResponse
from django.http.response import Http404
from django.shortcuts import redirect, render
from markdownx.utils import markdownify
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from content.models import Recipe, Article
from content.utils import generate_article_video_src
from srbc.decorators import validate_user, has_desktop_access


@login_required
@has_desktop_access
@validate_user
def recipes_list(request):
    if not request.user.profile.tariff or not request.user.profile.tariff.tariff_group.expertise_access:
        raise Http404()

    filter_tags = request.GET.get('tags')
    search_by = request.GET.get('q', '')
    recipes = Recipe.objects
    tags = []
    if filter_tags:
        tags = filter_tags.split(',')
        tags = list(set(tags))
        recipes = recipes.filter(tags__contains=tags)

    if search_by:
        recipes = recipes.filter(
            Q(title__icontains=search_by)
            | Q(body__icontains=search_by)
            | Q(comment__icontains=search_by)
        )

    recipes = recipes.all()
    page_num = request.GET.get('page')
    pager = Paginator(recipes, 20)

    try:
        recipes = pager.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        recipes = pager.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        recipes = pager.page(pager.num_pages)

    return render(
        request,
        'content/recipes_list.html',
        {
            'recipes': recipes,
            # 'pager': pager,
            'tags': tags,
            'q': search_by,
        }
    )


def article_page(request, article_slug):
    qs = Article.get_query_by_permission(user=request.user)
    try:
        article = qs.get(slug=article_slug)
    except ObjectDoesNotExist:
        raise Http404()

    article.text = markdownify(article.text)

    if article.has_video:
        article.video_src = generate_article_video_src(obj=article)

    if article.is_public:
        return get_article_public(request, article)
    else:
        return get_article_private(request, article)


def get_article_public(request, article):
    return render(
        request,
        'content/article_page.html',
        {
            'article': article,
        }
    )


@login_required
@has_desktop_access
@validate_user
def get_article_private(request, article):
    return render(
        request,
        'content/article_page.html',
        {
            'article': article,
        }
    )


def articles_list(request):
    qs = Article.get_query_by_permission(user=request.user)
    articles = qs.order_by('is_published', 'sort_num').all()

    return render(
        request,
        'content/articles_list.html',
        {
            'articles': articles,
        }
    )


def tos(request):
    return render(
        request,
        'content/static.html',
        {
            'page_slug': 'tos',
        }
    )


def tos_ru(request):
    return render(
        request,
        'content/static.html',
        {
            'page_slug': 'tos_ru',
        }
    )


def tos_ee(request):
    return render(
        request,
        'content/static.html',
        {
            'page_slug': 'tos_ee',
        }
    )


def privacy_en(request):
    return render(
        request,
        'content/static.html',
        {
            'page_slug': 'privacy_en',
        }
    )




@login_required
@has_desktop_access
@validate_user
@user_passes_test(lambda u: u.profile.agreement_signed_date, login_url='/agreement/', redirect_field_name='next')
def manual_download(request):
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


@login_required
@has_desktop_access
@validate_user
@user_passes_test(lambda u: u.profile.agreement_signed_date, login_url='/agreement/', redirect_field_name='next')
def measurements_download(request):
    path_to_assets = os.path.join(settings.BASE_DIR, "content", "assets", "manual")
    the_file = os.path.join(path_to_assets, "measurements_template.xlsx")

    filename = os.path.basename(the_file)
    filename = filename.replace('!!!', request.user.username)
    chunk_size = 8192
    response = StreamingHttpResponse(FileWrapper(open(the_file, 'rb'), chunk_size),
                                     content_type=mimetypes.guess_type(the_file)[0])
    response['Content-Length'] = os.path.getsize(the_file)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


@login_required
@has_desktop_access
@validate_user
def index(request):
    if request.user.is_staff:
        return redirect('/users/')

    return redirect('/dashboard/')

    # return redirect('/welcome/')
