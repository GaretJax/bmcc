from django.apps import apps
from django.conf import settings
from django.utils.functional import SimpleLazyObject


def get_celery_app():
    celery_app = getattr(settings, "CELERY_APP_CONFIG", "celery")
    return apps.get_app_config(celery_app).get_celery_app()


app = SimpleLazyObject(get_celery_app)
