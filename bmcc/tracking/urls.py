from django.urls import path

from . import views


app_name = "tracking"


urlpatterns = [
    path(
        "owntracks/",
        views.OwnTracksPingView.as_view(),
        name="owntracks_ping",
    ),
    path(
        "mission/<uuid:mission_id>/new/",
        views.OwnTracksRegisterView.as_view(),
        name="owntracks_register",
    ),
    path(
        "mission/<uuid:mission_id>/beacon/<uuid:beacon_id>/configuration/",
        views.OwnTracksConfigurationView.as_view(),
        name="owntracks_configuration",
    ),
    path(
        "mission/<uuid:mission_id>/beacon/<uuid:beacon_id>/configuration.json",
        views.OwnTracksConfigurationFileView.as_view(),
        name="owntracks_configuration_file",
    ),
]
