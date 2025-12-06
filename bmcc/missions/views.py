from django.db.models import OuterRef, Prefetch, Subquery
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView

import simplekml

from ..tracking import constants as tracking_constants
from ..tracking.models import Asset, Beacon, Ping
from . import models


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
