from django.urls import path

from . import views
from .views_asset_landing import asset_mark_landed
from .views_asset_launch import asset_mark_launched
from .views_predictions import run_launch_site_prediction


app_name = "missions"

urlpatterns = [
    path(
        "<uuid:mission_id>/", views.MissionDetailView.as_view(), name="detail"
    ),
    path(
        "<uuid:mission_id>/assets/",
        views.MissionAssetListView.as_view(),
        name="asset_list",
    ),
    path(
        "<uuid:mission_id>/assets/<uuid:asset_id>/",
        views.AssetDetailView.as_view(),
        name="asset_detail",
    ),
    path(
        "<uuid:mission_id>/assets/<uuid:asset_id>/mark-launched/",
        asset_mark_launched,
        name="asset_mark_launched",
    ),
    path(
        "<uuid:mission_id>/assets/<uuid:asset_id>/mark-landed/",
        asset_mark_landed,
        name="asset_mark_landed",
    ),
    path(
        "<uuid:mission_id>/parameters/",
        views.MissionParametersUpdateView.as_view(),
        name="mission_parameters",
    ),
    path(
        "<uuid:mission_id>/launch-sites/",
        views.LaunchSiteListView.as_view(),
        name="launch_site_list",
    ),
    path(
        "<uuid:mission_id>/launch-sites/<uuid:launch_site_id>/",
        views.LaunchSiteDetailView.as_view(),
        name="launch_site_detail",
    ),
    path(
        "<uuid:mission_id>/launch-sites/<uuid:launch_site_id>/edit/",
        views.LaunchSiteUpdateView.as_view(),
        name="launch_site_update",
    ),
    path(
        "<uuid:mission_id>/launch-sites/<uuid:launch_site_id>/predict/",
        run_launch_site_prediction,
        name="launch_site_predict",
    ),
    path(
        "<uuid:mission_id>/launch-sites/new/",
        views.LaunchSiteCreateView.as_view(),
        name="launch_site_create",
    ),
    path("<uuid:mission_id>.kml", views.kml_entrypoint, name="kml_entrypoint"),
    path(
        "<uuid:mission_id>-update.kml", views.kml_update, name="updating_kml"
    ),
]
