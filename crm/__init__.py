from django.apps import AppConfig


class CRMAppConfig(AppConfig):
    name = 'crm'
    verbose_name = 'CRM'


default_app_config = 'crm.CRMAppConfig'
