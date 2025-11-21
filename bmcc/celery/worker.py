import django
from django.apps import apps
from django.conf import settings


__all__ = ["celery"]

# Setup the django environment
django.setup()

# Load the celery app from the app config
celery_app = getattr(settings, "CELERY_APP_CONFIG", "celery")
celery = apps.get_app_config(celery_app).get_celery_app()
