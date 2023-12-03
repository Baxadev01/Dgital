from django.apps import AppConfig

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app', 'default_app_config')


class SRbCAppConfig(AppConfig):
    name = 'srbc'
    verbose_name = 'SRbC'


default_app_config = 'srbc.SRbCAppConfig'
