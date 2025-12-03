from django.db.models import Prefetch
from django.http import HttpResponse
from django.urls import reverse

import simplekml

from ..tracking import constants as tracking_constants
from ..tracking.models import Asset, Beacon, Ping
from . import models


ICON_BY_ASSET_TYPE = {
    tracking_constants.AssetType.BALLOON: (
        "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png"
    ),
    tracking_constants.AssetType.VEHICLE: (
        "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png"
    ),
}


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
    mission = models.Mission.objects.get(pk=mission_id)

    kml = simplekml.Kml()

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
    def build_coords(ping):
        if ping.altitude is not None:
            return (ping.longitude, ping.latitude, ping.altitude)
        return (ping.longitude, ping.latitude)

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

            coords = [build_coords(ping) for ping in pings]

            track = tracks_folder.newlinestring(
                name=beacon.identifier, coords=coords
            )
            track.altitudemode = "absolute"

            point = positions_folder.newpoint(
                name=beacon.identifier,
                gxaltitudemode="absolute",
                coords=coords[-1],
            )
            point.style.iconstyle.icon.href = ICON_BY_ASSET_TYPE.get(
                asset.asset_type,
                "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png",
            )

    response = HttpResponse(kml.kml())
    filename = f"{mission.pk}-update.kml"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
