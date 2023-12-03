from django.conf.urls import url
from srbc.views.api.v3.profiles import UserNoteListAPIView
from srbc.views.api.v3.checkpoints import UserPhotoUploadAPIView
from srbc.views.api.v3.diary import UserReportListAPIView
from srbc.views.api.v3.user import AuthByTelegram
from srbc.views.api.v3.admin import UserListAPIView, WaveListAPIView
from srbc.views.api.v3.prodamus import ProdamusPaymentAPIView

# FIXME
app_name = 'apps.srbc_api'


urlpatterns = [
    url(
        r'^profiles/usernote/$',
        UserNoteListAPIView.as_view(),
        name='user-note-list'
    ),
    url(
        r'^checkpoints/photos/$',
        UserPhotoUploadAPIView.as_view(),
        name='checkpoint-photos-upload'
    ),
    url(
        r'^diary/reports/$',
        UserReportListAPIView.as_view(),
        name='user-report-list'
    ),
    url(
        r'^auth/telegram/$',
        AuthByTelegram.as_view({
            'get': 'get_by_telegram',
        }),
        name='auth-user-telegram'
    ),
    url(
        r'^register/telegram/$',
        AuthByTelegram.as_view({
            'get': 'register_by_telegram',
        }),
        name='register-user-by-telegram'
    ),
    url(
        r'^staff/tools/users/$',
        UserListAPIView.as_view(),
        name='user-list'
    ),
    url(
        r'^staff/tools/waves/$',
        WaveListAPIView.as_view(),
        name='wave-list'
    ),
    url(
        r'^prodamus/payment/create/$',
        ProdamusPaymentAPIView.as_view(),
        name='prodamus-payment-create'
    )
    
    
]