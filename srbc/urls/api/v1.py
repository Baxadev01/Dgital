# -*- coding: utf-8 -*-
"""wifit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url

from srbc.views.api.v1.analytics import DiaryStatView, ReportView, ParseMealView
from srbc.views.api.v1.analysis import RegularAnalysis
from srbc.views.api.v1.diary import MealProductsSet, ParticipationGoalSet, DiaryRecordViewSet, \
    DiaryChartView, DiaryMealSet, CheckPointMeasurementSet, CheckpointPhotoSet, MealFaultSet, MealRecommendationsSet, \
    FullPointsDiaryChartView, DiaryNotReadySet
from srbc.views.api.v1.images import SRBCImagesListViewSet, IGImagesListViewSet, IGImagesSet, MealImageUploadView, \
    SRBCCustomImagesSet

from srbc.views.api.v1.celery import CeleryTaskView
from srbc.views.api.v1.staff import ProfileListViewSet, BookmarkToggleViewSet, AnalysisViewSet, NextMealViewSet
from srbc.views.api.v1.user import AuthByAppleToken, AuthByGoogleToken, AuthByFBToken, CurrentUserViewSet, ProfileItemViewSet
from srbc.views.api.v1.stripe import StripeSubscriptionCheckout, StripeSubscriptionChange 
from srbc.views.api.v1.yandex_kassa import YandexSubscriptionCreate
from srbc.views.api.v1.subscription import SubscriptionCancel
from srbc.views.api.v1.auth import JwtTemporaryToken
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from srbc.views.diary import load_tracker_data_mifit
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

# FIXME
app_name = 'apps.srbc_api'

decorated_obtain_jwt_token = swagger_auto_schema(
    method='post',
    **swagger_docs['POST /v1/auth/credentials/']
)(obtain_jwt_token)


decorated_refresh_jwt_token = swagger_auto_schema(
    method='post',
    **swagger_docs['POST /v1/auth/refresh/']
)(refresh_jwt_token) 

urlpatterns = [
    url(r'^auth/credentials/', decorated_obtain_jwt_token),
    url(r'^auth/refresh/', decorated_refresh_jwt_token),
    url(r'^auth/temporary/$', JwtTemporaryToken.as_view(), name='temporary-token'),

    url(r'^bookmarks/$', BookmarkToggleViewSet.as_view(), name='bookmark-toggle'),

    url(r'^profiles/(?P<user_id>[^/]+)/diary/chart/$', DiaryChartView.as_view(), name='diarybyprofile-chart'),

    url(r'^profiles/(?P<user_id>[^/]+)/diary/chart/full_points/$', FullPointsDiaryChartView.as_view(
        {
            "get": "get_stat",
        }
    ), name='fullpointsdiarybyprofile-chart'),

    url(r'^profiles/(?P<user_id>[^/]+)/diary/$', DiaryRecordViewSet.as_view(), name='diarybyprofile-list'),
    url(r'^users/current/$', CurrentUserViewSet.as_view(
        {
            "get": "get_current",
        }
    ), name='api-current-user'),
    url(r'^profiles/(?P<pk>[^/]+)/$', ProfileItemViewSet.as_view(), name='profile-detail'),
    url(r'^profiles/$', ProfileListViewSet.as_view(
        {
            'get': 'list',
        }
    ), name='profile-list'),
    url(r'^profiles/(?P<user_id>[0-9]+)/images/$', SRBCImagesListViewSet.as_view(
        {
            "get": "list_images",
        }
    ), name='img-list'),
    url(r'^profiles/(?P<user_id>[0-9]+)/ig/images/$', IGImagesListViewSet.as_view(), name='ig-list'),
    url(
        r'^profiles/(?P<user_id>[0-9]+)/ig/images/(?P<hashtag>[^/]+)/$',
        IGImagesSet.as_view(
            {
                "get": "get_by_hashtag",
            }
        ),
        name='ig-item'
    ),

    url(r'^images/meals/', MealImageUploadView.as_view(
        {
            "put": "upload",
        }
    )),

    url(
        r'^profiles/images/custom/$', SRBCCustomImagesSet.as_view(
            {
                "post": "upload_custom_image",
            }
        ),
        name='images-custom-self'
    ),
    url(
        r'^profiles/images/custom/(?P<image_id>[0-9]+)/$', SRBCCustomImagesSet.as_view(
            {
                "patch": "edit_custom_image"
            }
        ),
        name='images-custom-edit-self'
    ),

    url(
        r'^auth/facebook/',
        AuthByFBToken.as_view(
            {
                "get": "get_by_fb_token",
            }
        ),
        name='api-fb-auth'
    ),

    url(
        r'^auth/apple/',
        AuthByAppleToken.as_view(
            {
                "get": "get_by_apple_token",
            }
        ),
        name='api-apple-auth'
    ),
    url(
        r'^register/apple/',
        AuthByAppleToken.as_view(
            {
                "get": "register_by_apple_token",
            }
        ),
        name='api-apple-auth'
    ),

    url(
        r'^auth/google/',
        AuthByGoogleToken.as_view(
            {
                "get": "get_by_google_token",
            }
        ),
        name='api-google-auth'
    ),

    url(
        r'^register/google/',
        AuthByGoogleToken.as_view(
            {
                "get": "register_by_google_token",
            }
        ),
        name='api-google-register'
    ),



    url(r'^tracker/mifit/load/$', load_tracker_data_mifit, name='mifit-linkpage'),
    url(r'^tracker/mifit/load/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$', load_tracker_data_mifit,
        name='mifit-linkpage-date'),

    url(
        r'^diary/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meals/$', DiaryMealSet.as_view(
            {
                "get": "meals_get",
                "put": "meals_upsert",
            }),
        name='diary-meals-item'
    ),

    url(r'^meals/recommendations/$', MealRecommendationsSet.as_view(), name='meals-recommendations'),

    url(
        r'^diary/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meals/image/(?P<meal_dt>[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}:[0-9]{2})/$',
        DiaryMealSet.as_view(
            {
                "put": "meals_images_upsert",
                "delete": "meals_images_delete",
            }),
        name='diary-meals-images-item'
    ),
    url(
        r'^diary/(?P<diary_user>[0-9]+)/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$', DiaryMealSet.as_view(
            {
                "get": "diary_get",
            }),
        name='diary-item-get'
    ),
    url(
        r'^diary/(?P<diary_user>[0-9]+)/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meals/$', DiaryMealSet.as_view(
            {
                "get": "meals_get_admin",
                "put": "meals_review",
            }),
        name='diary-meals-item-review'
    ),
    url(
        r'^diary/(?P<diary_user>[0-9]+)/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/data/$', DiaryMealSet.as_view(
            {
                "patch": "data_upsert",
            }),
        name='diary-data-item-upsert'
    ),

    url(
        r'^diary/(?P<user_id>[0-9]+)/stat/meals/', DiaryStatView.as_view(
            {
                "get": "get_meals_faults_stat",
            }

        ),
        name='diary-meals-stat-faults'
    ),

    url(r'^analysis/(?P<user_id>[0-9]+)/regular/$', RegularAnalysis.as_view(), name='analysis-regular'),

    url(
        r'^diary/(?P<user_id>[0-9]+)/stat/user/', DiaryStatView.as_view(
            {
                "get": "get_user_stat",
            }

        ),
        name='diary-user-stat'
    ),
    url(
        r'^diary/(?P<user_id>[0-9]+)/stat/report/', ReportView.as_view(
            {
                "get": "get_stat_report_admin",
            }

        ),
        name='diary-meals-stat-faults'
    ),

    # url(
    #     r'diary/(?P<user_id>[0-9]+)/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/data/', DiaryRecordSet.as_view(
    #         {
    #             "put": "data_upsert",
    #         }),
    #     name='diary-data-upsert'
    # ),
    url(
        r'^diary/faults/', MealFaultSet.as_view(
            {
                "get": "get_list",
            }
        ),
        name='api-meal-faults-list'
    ),
    url(
        r'^diary/not-ready/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$', DiaryNotReadySet.as_view(
            {
                "get": "get_not_ready_list",
            }
        ),
        name='api-not-ready-diaries-list'
    ),
    url(
        r'^diary/products/$', MealProductsSet.as_view(
            {
                "get": "search",
            }
        ),
        name='api-meal-products-list'
    ),
    url(
        r'^diary/products/wiki/$', MealProductsSet.as_view(
            {
                "get": "check_new",
            }
        ),
        name='api-meal-products-wiki'
    ),
    url(
        r'^staff/tools/next_meal/$', NextMealViewSet.as_view(
            {
                "get": "get_next_meal",
            }
        ),
        name='api-staff-tools-nextmeal'
    ),

    # === staff analysis
    
    # url(
    #     r'^diaries/(?P<diary_id>[0-9]+)/meal_review/$', ParseMealView.as_view(
    #         {
    #             "get": "get_meal_faults",
    #         }),
    #     name='diary-meal-analysis-set'
    # ),
    url(
        r'^user/(?P<user_id>[0-9]+)/diaries/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meal_review/$',
        ParseMealView.as_view(
            {
                "get": "get_meal_faults_by_date",
            }),
        name='diary-meal-analysis-by-date-set'
    ),
    url(
        r'^user/(?P<user_id>[0-9]+)/diaries/(?P<diary_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meal_stat/$',
        ParseMealView.as_view(
            {
                "get": "get_meal_stat_by_date",
            }),
        name='diary-meal-stat-analysis-by-date-set'
    ),
    url(
        r'^profile/(?P<user_id>[0-9]+)/analysis/templates/$', AnalysisViewSet.as_view(
            {
                "get": "get_analysis_templates",
            }),
        name='profile-analysis-set'
    ),
    url(
        r'^profile/(?P<user_id>[0-9]+)/analysis/add/$', AnalysisViewSet.as_view(
            {
                "post": "add_analysis_recommendation",
            }),
        name='profile-analysis-set'
    ),

    # === measurement checkpoints ===
    url(
        r'^checkpoints/(?P<user_id>[0-9]+)/measurements/$', CheckPointMeasurementSet.as_view(
            {
                "get": "get_measurements_admin",
            }
        ), name='api-checkpoint-measurement'
    ),
    url(
        r'^checkpoints/(?P<user_id>[0-9]+)/measurements/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$',
        CheckPointMeasurementSet.as_view(
            {
                "get": "get_measurement_admin",
                "post": "create_measurement_admin",
                "patch": "update_measurement_admin",
                "delete": "delete_measurement_admin",
            }
        ), name='api-checkpoint-measurement-by-date'
    ),
    url(
        r'^checkpoints/(?P<user_id>[0-9]+)/photos/', CheckpointPhotoSet.as_view(
            {
                "get": "photos_get_admin",
                "patch": "photos_crop_admin",
                "put": "collage_build_admin",
            }
        ), name='api-checkpoints-photo'
    ),

    url(
        r'^checkpoints/measurements/$', CheckPointMeasurementSet.as_view(
            {
                "get": "get_measurements",
            }
        ), name='api-checkpoint-measurement-self'
    ),
    url(
        r'^checkpoints/measurements/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$',
        CheckPointMeasurementSet.as_view(
            {
                "get": "get_measurement",
                "post": "create_measurement",
                "patch": "update_measurement",
                "delete": "delete_measurement",
            }
        ), name='api-checkpoint-measurement-by-date-self'
    ),
    url(
        r'^checkpoints/photos/', CheckpointPhotoSet.as_view(
            {
                "get": "photos_get",
                "patch": "photos_crop",
                "put": "collage_build",
            }
        ), name='api-checkpoints-photo-self'
    ),
    url(
        r'^goals/$', ParticipationGoalSet.as_view(
            {
                "get": "get_all",
                "post": "add_goal",
            }
        ), name='api-participiant-goals'
    ),
    url(
        r'^goals/(?P<goal_id>[0-9]+)/$', ParticipationGoalSet.as_view(
            {
                "patch": "edit_status",
            }
        ), name='api-participiant-goal'
    ),
    url(r'^tasks/(?P<task_id>[^/]+)/$', CeleryTaskView.as_view(), name='diarybyprofile-chart'),

    url(r'^stripe/subscription/create/checkout/$', StripeSubscriptionCheckout.as_view(),
        name='stripe-subscription-create-checkout'),
    url(r'^stripe/subscription/change/$', StripeSubscriptionChange.as_view(),
        name='stripe-subscription-change-checkout'),
    url(r'^yandex/subscription/create/checkout/$', YandexSubscriptionCreate.as_view(),
        name='yandex-subscription-create-checkout'),
        
    url(r'^subscription/cancel/$', SubscriptionCancel.as_view(),
        name='subscription-cancel'),
]
