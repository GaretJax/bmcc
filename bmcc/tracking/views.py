from django import http

from . import constants, models


def owntracks_ping(request):
    beacon = (
        models.Beacon.objects.active()
        .filter(backend_class_path=constants.BeaconBackendClass.OWNTRACKS)
        .first()
    )

    if beacon:
        beacon.backend.handle_ping(beacon, {})

    return http.HttpResponse()
