from django.db.models import OuterRef, Prefetch, Subquery
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, FormView, ListView

import simplekml

from bmcc.predictions.models import Prediction

from ..tracking import constants as tracking_constants
from ..tracking.models import Asset, Beacon, Ping
from . import models
from .forms import (
    LaunchSiteForm,
    LaunchSiteUpdateForm,
    MissionParametersForm,
)
from .models import LaunchSite


ICON_BY_ASSET_TYPE = {
    tracking_constants.AssetType.BALLOON: (
        "http://maps.google.com/mapfiles/kml/paddle/purple-blank.png"
    ),
    tracking_constants.AssetType.VEHICLE: (
        "http://maps.google.com/mapfiles/kml/shapes/woman.png"
    ),
}


class MissionDetailView(DetailView):
    queryset = models.Mission.objects.prefetch_related(
        "launch_site_candidates"
    )
    template_name = "missions/mission_detail.html"
    context_object_name = "mission"
    pk_url_kwarg = "mission_id"

    def get_assets(self):
        return list(
            self.object.assets.order_by("asset_type", "name").prefetch_related(
                Prefetch(
                    "beacons",
                    queryset=Beacon.objects.order_by(
                        "identifier"
                    ).prefetch_related(
                        Prefetch(
                            "pings",
                            queryset=Ping.objects.filter(
                                mission=self.object
                            ).order_by("-reported_at", "-created_at")[:1],
                            to_attr="latest_ping",
                        )
                    ),
                )
            )
        )

    def get_context_data(self, **kwargs):
        assets = self.get_assets()
        kwargs.update(
            {
                "assets": assets,
                "beacon_count": sum(len(a.beacons.all()) for a in assets),
            }
        )
        return super().get_context_data(**kwargs)


class MissionAssetListView(ListView):
    model = Asset
    template_name = "tracking/assets_list.html"
    context_object_name = "assets"

    def get_queryset(self):
        self.mission = models.Mission.objects.get(pk=self.kwargs["mission_id"])
        latest_ping = Ping.objects.filter(asset=OuterRef("pk")).order_by(
            "-reported_at", "-created_at"
        )
        return (
            Asset.objects.filter(mission=self.mission)
            .select_related("mission")
            .annotate(
                last_ping_reported_at=Subquery(
                    latest_ping.values("reported_at")[:1]
                ),
                last_ping_position=Subquery(
                    latest_ping.values("position")[:1]
                ),
                last_ping_altitude=Subquery(
                    latest_ping.values("altitude")[:1]
                ),
                last_ping_beacon=Subquery(
                    latest_ping.values("beacon__identifier")[:1]
                ),
            )
            .order_by("name")
        )

    def get_context_data(self, **kwargs):
        kwargs["mission"] = self.mission
        kwargs["refreshed_at"] = timezone.now()
        return super().get_context_data(**kwargs)

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            return ["tracking/partials/assets_table.html"]
        return [self.template_name]


class AssetDetailView(DetailView):
    model = Asset
    template_name = "tracking/asset_detail.html"
    context_object_name = "asset"
    pk_url_kwarg = "asset_id"

    def get_queryset(self):
        return (
            Asset.objects.select_related("mission")
            .prefetch_related("beacons", "beacons__pings")
            .filter(mission__pk=self.kwargs["mission_id"])
        )

    def get_context_data(self, **kwargs):
        mission = self.object.mission
        kwargs["mission"] = mission
        ping_qs = Ping.objects.filter(asset=self.object)
        if mission.mission_window:
            if mission.mission_window.lower:
                ping_qs = ping_qs.filter(
                    reported_at__gte=mission.mission_window.lower
                )
            if mission.mission_window.upper:
                ping_qs = ping_qs.filter(
                    reported_at__lte=mission.mission_window.upper
                )
        kwargs["pings"] = ping_qs.order_by(
            "-reported_at", "-created_at"
        ).select_related("beacon")[:10]
        altitude_series = {}
        speed_series = {}
        kwargs["chart_bounds"] = {
            "start": mission.mission_window.lower
            if mission.mission_window
            else None,
            "end": mission.mission_window.upper
            if mission.mission_window
            else None,
        }
        beacon_data = ping_qs.order_by("reported_at").values_list(
            "beacon__identifier", "reported_at", "altitude", "position"
        )
        horizontal_series = {}
        for beacon_id, reported_at, altitude, position in beacon_data:
            altitude_series.setdefault(beacon_id, []).append(
                (reported_at, altitude)
            )
            history = speed_series.setdefault(beacon_id, [])
            history.append((reported_at, altitude, position))
            horizontal_series.setdefault(beacon_id, []).append(
                (reported_at, position)
            )

        speed_chart_data = {}
        for beacon_id, points in speed_series.items():
            derived = []
            for idx in range(1, len(points)):
                prev_t, prev_alt, _ = points[idx - 1]
                curr_t, curr_alt, _ = points[idx]
                if prev_alt is None or curr_alt is None:
                    continue
                delta_alt = curr_alt - prev_alt
                delta_t = (curr_t - prev_t).total_seconds()
                if delta_t <= 0:
                    continue
                derived.append((curr_t, delta_alt / delta_t))
            speed_chart_data[beacon_id] = derived

        def haversine_meters(p1, p2):
            import math

            lat1, lon1 = math.radians(p1.y), math.radians(p1.x)
            lat2, lon2 = math.radians(p2.y), math.radians(p2.x)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return 6371000 * c

        horizontal_chart_data = {}
        for beacon_id, points in horizontal_series.items():
            derived = []
            for idx in range(1, len(points)):
                prev_t, prev_pos = points[idx - 1]
                curr_t, curr_pos = points[idx]
                delta_t = (curr_t - prev_t).total_seconds()
                if delta_t <= 0 or not prev_pos or not curr_pos:
                    continue
                distance = haversine_meters(prev_pos, curr_pos)
                derived.append((curr_t, distance / delta_t))
            horizontal_chart_data[beacon_id] = derived

        kwargs["altitude_series"] = altitude_series
        kwargs["speed_series"] = speed_chart_data
        kwargs["horizontal_speed_series"] = horizontal_chart_data
        kwargs["refreshed_at"] = timezone.now()
        return super().get_context_data(**kwargs)

    def get_template_names(self):
        if getattr(self.request, "htmx", False):
            section = self.request.headers.get(
                "HX-Section"
            ) or self.request.GET.get("hx_section")
            if section == "altitude":
                return ["tracking/partials/asset_altitude_chart.html"]
            if section == "speed":
                return ["tracking/partials/asset_speed_chart.html"]
            if section == "horizontal_speed":
                return ["tracking/partials/asset_horizontal_speed_chart.html"]
            if section == "pings":
                return ["tracking/partials/asset_pings_table.html"]
            return ["tracking/partials/asset_pings_table.html"]
        return [self.template_name]


class LaunchSiteListView(ListView):
    model = LaunchSite
    template_name = "missions/launch_sites.html"
    context_object_name = "launch_sites"

    def get_queryset(self):
        self.mission = models.Mission.objects.get(pk=self.kwargs["mission_id"])
        return LaunchSite.objects.filter(mission=self.mission).order_by("name")

    def get_context_data(self, **kwargs):
        kwargs["mission"] = self.mission
        return super().get_context_data(**kwargs)


class LaunchSiteDetailView(DetailView):
    model = LaunchSite
    template_name = "missions/launch_site_detail.html"
    context_object_name = "launch_site"
    pk_url_kwarg = "launch_site_id"

    def get_queryset(self):
        return (
            LaunchSite.objects.filter(mission_id=self.kwargs["mission_id"])
            .select_related("mission")
            .prefetch_related(
                Prefetch(
                    "prediction_history",
                    queryset=Prediction.objects.order_by("-created_at"),
                )
            )
        )

    def get_context_data(self, **kwargs):
        kwargs["mission"] = self.object.mission
        preds = self.object.prediction_history.all()
        kwargs["last_prediction"] = preds[0] if preds else None
        return super().get_context_data(**kwargs)


class LaunchSiteCreateView(DetailView, FormView):
    model = models.Mission
    form_class = LaunchSiteForm
    template_name = "missions/launch_site_form.html"
    pk_url_kwarg = "mission_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs["mission"] = self.object
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = kwargs.get("initial") or {}
        return kwargs

    def form_valid(self, form):
        launch_site = form.save(commit=False)
        launch_site.mission = self.object
        launch_site.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "missions:launch_site_list",
            kwargs={"mission_id": self.object.pk},
        )


class LaunchSiteUpdateView(DetailView, FormView):
    model = LaunchSite
    form_class = LaunchSiteUpdateForm
    template_name = "missions/launch_site_update_form.html"
    pk_url_kwarg = "launch_site_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return LaunchSite.objects.filter(
            mission_id=self.kwargs["mission_id"]
        ).select_related("mission")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs["mission"] = self.object.mission
        kwargs["launch_site"] = self.object
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "missions:launch_site_detail",
            kwargs={
                "mission_id": self.kwargs["mission_id"],
                "launch_site_id": self.object.pk,
            },
        )


class MissionParametersUpdateView(DetailView, FormView):
    model = models.Mission
    form_class = MissionParametersForm
    template_name = "missions/mission_parameters_form.html"
    pk_url_kwarg = "mission_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        return kwargs

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        kwargs["mission"] = self.object
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse(
            "missions:detail", kwargs={"mission_id": self.object.pk}
        )


def kml_entrypoint(request, mission_id):
    mission = models.Mission.objects.get(pk=mission_id)

    kml = simplekml.Kml()
    netlink = kml.newnetworklink(
        name=mission.name,
    )
    netlink.link.href = request.build_absolute_uri(
        reverse("missions:updating_kml", kwargs={"mission_id": mission.pk})
    )
    netlink.link.refreshmode = "onInterval"
    netlink.link.refreshinterval = 10

    response = HttpResponse(kml.kml())
    filename = f"{mission.pk}.kml"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def kml_update(request, mission_id):
    mission = models.Mission.objects.prefetch_related(
        "launch_site_candidates"
    ).get(pk=mission_id)

    kml = simplekml.Kml()

    launch_sites_folder = kml.newfolder(name="Launch sites")

    assets = (
        Asset.objects.filter(mission=mission)
        .select_related("mission")
        .prefetch_related(
            Prefetch(
                "beacons",
                queryset=Beacon.objects.active().prefetch_related(
                    Prefetch(
                        "pings",
                        queryset=Ping.objects.filter(mission=mission).order_by(
                            "reported_at"
                        ),
                    )
                ),
            )
        )
        .order_by("asset_type", "name")
    )

    type_folders = {}

    # Normalize coordinates to 2D or 3D based on altitude availability
    def build_coords(longitude, latitude, altitude):
        if altitude is not None:
            return (longitude, latitude, altitude)
        return (longitude, latitude)

    for asset in assets:
        type_folder = type_folders.get(asset.asset_type)
        if type_folder is None:
            root_folder = kml.newfolder(name=asset.get_asset_type_display())
            type_folder = {
                "root": root_folder,
                "tracks": root_folder.newfolder(name="Tracks"),
                "positions": root_folder.newfolder(name="Current Positions"),
            }
            type_folders[asset.asset_type] = type_folder

        tracks_folder = type_folder["tracks"].newfolder(name=str(asset))
        positions_folder = type_folder["positions"].newfolder(name=str(asset))

        for beacon in asset.beacons.all():
            pings = list(beacon.pings.all())
            if not pings:
                continue

            coords = [
                build_coords(ping.longitude, ping.latitude, ping.altitude)
                for ping in pings
            ]

            kwargs = {}
            if any(c[2] for c in coords):
                kwargs["altitudemode"] = "absolute"
                kwargs["gxaltitudemode"] = "absolute"
            else:
                kwargs["altitudemode"] = "clampToGround"
                kwargs["gxaltitudemode"] = "clampToGround"

            track = tracks_folder.newlinestring(
                name=beacon.identifier,
                coords=coords,
                visibility=(
                    asset.asset_type == tracking_constants.AssetType.BALLOON
                ),
                **kwargs,
            )
            if asset.asset_type == tracking_constants.AssetType.BALLOON:
                track.extrude = 1
                track.tessellate = 1
                track.style.linestyle.color = "7f800080"
                track.style.linestyle.width = 4
                track.style.polystyle.color = "7f800080"
            track.style.iconstyle.icon.href = ICON_BY_ASSET_TYPE.get(
                asset.asset_type,
                "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png",
            )

            point = positions_folder.newpoint(
                name=beacon.identifier,
                altitudemode="absolute",
                gxaltitudemode="absolute",
                coords=[coords[-1]],
            )
            point.style.iconstyle.icon.href = ICON_BY_ASSET_TYPE.get(
                asset.asset_type,
                "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png",
            )

    for launch_site in mission.launch_site_candidates.all():
        site_folder = launch_sites_folder.newfolder(name=launch_site.name)
        coords = [
            build_coords(
                launch_site.location.x,
                launch_site.location.y,
                launch_site.altitude,
            )
        ]
        point = site_folder.newpoint(
            name=launch_site.name, coords=coords, gxaltitudemode="absolute"
        )

    response = HttpResponse(kml.kml())
    filename = f"{mission.pk}-update.kml"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
