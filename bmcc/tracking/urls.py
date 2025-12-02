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
        "owntracks/mission/<uuid:pk>/new/",
        views.OwnTracksRegisterView.as_view(),
        name="owntracks_register",
    ),
    path(
        "owntracks/beacon/<uuid:pk>/configuration/",
        views.OwnTracksConfigurationView.as_view(),
        name="owntracks_configuration",
    ),
    path(
        "owntracks/beacon/<uuid:pk>/configuration.otrc",
        views.OwnTracksConfigurationFileView.as_view(),
        name="owntracks_configuration_file",
    ),
    path("api/<uuid:pk>/ping/", views.BeaconUpdateView.as_view()),
]
