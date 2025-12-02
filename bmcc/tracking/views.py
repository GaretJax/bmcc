import json

from django.contrib.gis.geos import Point
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import UpdateView

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

    return HttpResponse()


@method_decorator(csrf_exempt, name="dispatch")
class BeaconUpdateView(UpdateView):
    model = models.Beacon
    queryset = models.Beacon.objects.active().filter(
        backend_class_path=constants.BeaconBackendClass.BMCC_API
    )
    fields = []

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        self.object = self.get_object()

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        position = Point(
            float(payload["longitude"]), float(payload["latitude"])
        )
        altitude = payload.get("altitude")
        altitude = float(altitude) if altitude else None

        ping = self.object.pings.create(
            asset=self.object.asset,
            mission=self.object.asset.mission,
            position=position,
            altitude=altitude,
            reported_at=timezone.now(),
            metadata=payload,
        )

        return JsonResponse({"status": "ok", "ping": ping.pk}, status=201)
