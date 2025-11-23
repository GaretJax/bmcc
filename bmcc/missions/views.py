from django.http import HttpResponse
from django.urls import reverse

import simplekml

from ..tracking.models import Beacon
from . import models


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

    for beacon in Beacon.objects.active().filter(asset__mission=mission):
        ping = beacon.pings.order_by("-created_at").first()
        if ping:
            kml.newpoint(
                name=beacon.identifier,
                gxaltitudemode="relativeToSeaFloor",
                coords=[(ping.position.x, ping.position.y, ping.altitude)],
            )

    response = HttpResponse(kml.kml())
    filename = f"{mission.pk}-update.kml"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
