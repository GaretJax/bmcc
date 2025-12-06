from django.urls import path

from . import views_asset_landing


urlpatterns = [
    path(
        "missions/<uuid:mission_id>/assets/<uuid:asset_id>/land/",
        views_asset_landing.asset_mark_landed,
        name="asset_mark_landed",
    ),
]
