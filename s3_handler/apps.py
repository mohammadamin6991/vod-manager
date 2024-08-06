''' import app config module '''
from django.apps import AppConfig


class S3HandlerConfig(AppConfig):
    ''' app config class '''
    default_auto_field = 'django.db.models.BigAutoField'
    name = 's3_handler'
