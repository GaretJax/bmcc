from django.apps import AppConfig, apps

from celery import Celery


class DefaultConfig(AppConfig):
    name = "bmcc.celery"
    verbose_name = "Celery integration"

    def init_app(self):
        def iter_app_paths():
            for app in apps.get_app_configs():
                yield app.name

        # Setup celery
        self._celery_app = Celery("bmcc")
        self._celery_app.config_from_object(
            "django.conf:settings", namespace="CELERY"
        )
        self._celery_app.autodiscover_tasks(iter_app_paths, force=True)

    def ready(self):
        self.init_app()

    def get_celery_app(self):
        return self._celery_app
