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

from srbc.views.admin import meal_admin_stream, meal_admin_stream_go, \
    add_regular_analysis_old, product_moderation, MealProductAutocomplete, \
    users_list_new as users_list, diaries_form, user_diaries_form, meal_admin, \
    users_list_autoanalize, facebook_profile_link, renewal_request_management, add_regular_analysis, shortcuts, sale_prodamus


from srbc.views.auth import logout_view, login_form, registration, application_form, social_register, welcome, \
    blocked_user, link_instagram_secure, agreement_sign, tariff_selection, link_telegram, \
    admission_required, payment, user_username, user_names, mobile_tariff, auth_mobile, desktop_no_access, tg_login_view
from srbc.views.collage import data_collage_gen, data_collage_page
from srbc.views.diary import user_day_data_form,  user_day_meals_form, user_photo_upload, \
    checkpoint_measurements_app, checkpoint_photos_app
from srbc.views.participant import dashboard, profile, load_true_weight, link_mifit, profile_settings, user_notes, \
    result_reports, result_report_get

app_name = 'apps.srbc'

urlpatterns = [
    url(r'^logout/$', logout_view),
    url(r'^accounts/login/$', login_form),
    url(r'^accounts/login/tg/$', tg_login_view),
    url(r'^accounts/registration/$', registration),
    url(r'^auth/mobile/$', auth_mobile, name='auth-mobile'),

    url(r'^welcome/$', welcome, name='welcome-page'),
    url(r'^blocked/$', blocked_user, name='blocked-page'),
    url(r'^blocked/mobile/$', mobile_tariff, name='blocked-mobile-page'),
    url(r'^blocked/desktop/no-access/$', desktop_no_access, name='blocked-desktop-no-access'),
    url(r'^payment/$', payment, name='paywall'),
    url(r'^names/$', user_names, name='registration-names-page'),
    url(r'^username/$', user_username, name='registration-username-page'),

    url(r'^agreement/$', agreement_sign, name='agreement-page'),

    url(r'^application/$', application_form, name='application-page'),

    url(r'^instagram/(?P<userkey>[A-F0-9a-f]{96})/$',
        link_instagram_secure, name="instagram-link-secure"),
    url(r'^telegram/$', link_telegram, name='telegram-linkpage'),
    url(r'^admission/$', admission_required, name='admission-wallpage'),

    url(r'^trueweight/$', load_true_weight, name='trueweight-ie'),

    url(r'^tracker/mifit/$', link_mifit, name='mifit-linkpage'),

    url(r'^tariff/$', tariff_selection, name='tariff-page'),

    url(r'^social/register/(?P<backend>[a-zA-Z0-9_.-]+)/$', social_register, name='social-register'),
    url(r'^checkpoints/measurements/', checkpoint_measurements_app, name='measurements-webapp'),
    url(r'^checkpoints/photos/', checkpoint_photos_app, name='measurements-webapp'),
    url(r'^diary/(?P<data_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meals/$', user_day_meals_form, name='diary-meals'),
    url(r'^diary/(?P<data_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/data/$', user_day_data_form, name='diary-data'),
    url(r'^diary/today/meals/$', user_day_meals_form, name='diary-meals-redir'),
    url(r'^diary/today/data/$', user_day_data_form, name='diary-data-redir'),
    # url(r'^diary/(?P<data_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meals/$', user_day_meals_form, name='diary-meals'),
    url(r'^diary/(?P<data_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/data/collage/$', data_collage_page, name='collage-data'),
    url(r'^diary/today/data/collage/$', data_collage_page, name='collage-data-redir'),
    url(r'^diary/(?P<data_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/data.jpg$', data_collage_gen, name='collage-data-img'),

    url(r'^settings/$', profile_settings, name='profile_settings'),
    url(r'^photos/$', user_photo_upload, name='user-photo-upload'),

    url(r'^users/$', users_list, name='users'),
    url(r'^users/analize/$', users_list_autoanalize, name='users_analize'),

    url(r'^diaries/$', diaries_form, name='diaries'),

    url(r'^dashboard/$', dashboard, name='dashboard'),
    url(r'^notes/$', user_notes, name='notes-page'),
    url(r'^reports/$', result_reports, name='stat-reports-page'),
    url(r'^reports/(?P<hashid>[a-zA-Z0-9]+)/download/$', result_report_get, name='stat-reports-page-redirect'),

    url(r'^profile/(?P<username>[a-zA-Z0-9_.!-]+)/$', profile, name='profile-single'),
    url(r'^profile/(?P<username>[a-zA-Z0-9_.!-]+)/diaries/$', user_diaries_form, name='profile-diaries'),
    url(r'^profile/(?P<username>[a-zA-Z0-9_.!-]+)/diaries/meals/$', meal_admin, name='profile-diaries-meals'),
    url(r'^user/(?P<user_id>[0-9]+)/diaries/(?P<meal_date>[0-9]{4}-[0-9]{2}-[0-9]{2})/meal/$',
        meal_admin_stream, name='profile-diaries-meals-stream'),
    url(r'^profile/(?P<user_id>[0-9]+)/facebook/$', facebook_profile_link, name='profile-facebook-link'),
    url(r'^profile/(?P<user_id>[0-9]+)/analysis/add/$', add_regular_analysis_old, name='profile-analysis-add-old'),
    url(r'^profile/(?P<user_id>[0-9]+)/analysis/new/$', add_regular_analysis, name='profile-analysis-add'),
    url(r'^profile/$', profile, name='profile'),
    url(r'^renewal/(?P<rrid>[0-9]+)/$', renewal_request_management, name='renewal-request-manage'),

    # TODO: Move all staff urls here
    url(r'^staff/meal_products/$', product_moderation, name='staff-meal-product-moderation'),
    url(r'^staff/meal_review/$', meal_admin_stream_go, name='staff-meal-review-go'),
    url(r'^staff/shortcuts/$', shortcuts, name='staff-shortcuts'),
    url(r'^staff/sale-prodamus/$', sale_prodamus, name='sale-prodamus'),
    url(r'^staff/meal_products/products-autocomplete/$', MealProductAutocomplete.as_view(),
        name='staff-meal-product-moderation-search'),
]
