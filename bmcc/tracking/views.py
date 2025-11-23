import json

from django import http
from django.views.decorators.csrf import csrf_exempt

from . import constants, models


@csrf_exempt
def owntracks_ping(request):
    beacon = (
        models.Beacon.objects.active()
        .filter(backend_class_path=constants.BeaconBackendClass.OWNTRACKS)
        .first()
    )

    if beacon:
        beacon.backend.handle_ping(beacon, json.loads(request.body))

    return http.HttpResponse()
