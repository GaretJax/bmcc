from django.urls import path

from . import views


app_name = "missions"

urlpatterns = [
    path("<uuid:mission_id>.kml", views.kml_entrypoint),
    path(
        "<uuid:mission_id>-update.kml", views.kml_update, name="updating_kml"
    ),
]
