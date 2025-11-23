from django.urls import path

from . import views


urlpatterns = [
    path(
        "owntracks/",
        views.owntracks_ping,
    )
]
