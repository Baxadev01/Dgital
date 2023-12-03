from django.conf import settings


def mobile_app_login(request):
    return {
        'MOBILE_DEEPLINK': settings.MOBILE_DEEPLINK,
        'APPLE_STORE_PATH': settings.APPLE_STORE_PATH,
        'ANDROID_STORE_PATH': settings.ANDROID_STORE_PATH,
    }
