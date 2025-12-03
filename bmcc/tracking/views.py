import base64
import json
import logging

from django import http
from django.contrib.gis.geos import Point
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, UpdateView
from django.views.generic.edit import ModelFormMixin

from . import constants, forms, models


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class OwnTracksPingView(View):
    def post(self, request, *args, **kwargs):
        body = request.body
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning(
                "OwnTracks payload is not valid JSON",
                exc_info=True,
                extra={
                    "path": request.path,
                    "body_preview": body[:200].decode("utf-8", "replace"),
                    "content_length": len(body),
                },
            )
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        msg_type = data.get("_type")
        if msg_type != "location":
            logger.warning(
                "OwnTracks message ignored (non-location)",
                extra={
                    "msg_type": msg_type,
                    "topic": data.get("topic"),
                    "payload_keys": sorted(data.keys()),
                },
            )
            return http.JsonResponse({}, status=200)
            # return http.JsonResponse(
            #     {"unknown_message_type": msg_type}, status=400
            # )

        topic = data.get("topic", "")
        identifier = topic.rsplit("/", 1)[-1]

        if not identifier:
            logger.error(
                "OwnTracks payload missing beacon identifier",
                extra={
                    "topic": topic,
                    "payload_keys": sorted(data.keys()),
                },
            )
            return JsonResponse(
                {"error": "Missing beacon identifier"}, status=400
            )

        beacon = (
            models.Beacon.objects.active()
            .filter(
                backend_class_path=constants.BeaconBackendClass.OWNTRACKS,
                pk=identifier,
            )
            .first()
        )

        if not beacon:
            logger.warning(
                "OwnTracks beacon not found or inactive",
                extra={
                    "identifier": identifier,
                    "topic": topic,
                },
            )
            return http.JsonResponse({}, status=200)

        try:
            ping, response = beacon.backend.handle_ping(data)
        except Exception:
            logger.exception(
                "OwnTracks backend failed to handle ping",
                extra={
                    "beacon_id": str(beacon.id),
                    "identifier": identifier,
                    "payload": data,
                },
            )
            return JsonResponse(
                {"error": "Could not process ping"}, status=500
            )

        logger.debug(
            "OwnTracks ping processed",
            extra={
                "beacon_id": str(beacon.id),
                "ping_id": str(ping.id),
            },
        )

        return http.JsonResponse(response, safe=False)


class OwnTracksRegisterView(UpdateView):
    model = models.Mission
    template_name = "tracking/owntracks_register.html"
    form_class = forms.OwnTracksRegistrationForm

    def get_form_kwargs(self):
        return super(ModelFormMixin, self).get_form_kwargs()

    def form_valid(self, form):
        _, beacon = form.create_objects(self.object)
        return redirect("tracking:owntracks_configuration", pk=beacon.pk)


class OwnTracksConfigurationView(DetailView):
    queryset = models.Beacon.objects.filter(
        backend_class_path=constants.BeaconBackendClass.OWNTRACKS
    )
    template_name = "tracking/owntracks_configuration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self.object.backend.get_config()
        config_url = self.request.build_absolute_uri(
            reverse(
                "tracking:owntracks_configuration_file",
                kwargs={"pk": self.object.id},
            )
        )
        config_json = json.dumps(config, indent=2)
        config_payload = base64.b64encode(
            json.dumps(config).encode("utf-8")
        ).decode("ascii")
        owntracks_url = f"owntracks:///config?inline={config_payload}"
        context.update(
            {
                "config": config,
                "config_json": config_json,
                "config_url": config_url,
                "owntracks_url": owntracks_url,
            }
        )
        return context


class OwnTracksConfigurationFileView(DetailView):
    queryset = models.Beacon.objects.filter(
        backend_class_path=constants.BeaconBackendClass.OWNTRACKS
    )

    def get(self, request, *args, **kwargs):
        return http.JsonResponse(self.get_object().backend.get_config())


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
