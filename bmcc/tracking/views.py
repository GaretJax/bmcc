import base64
import json

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


@method_decorator(csrf_exempt, name="dispatch")
class OwnTracksPingView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        msg_type = data.get("_type")
        if msg_type != "location":
            return http.JsonResponse(
                {"unknown_message_type": msg_type}, status=400
            )

        topic = data.get("topic", "")
        identifier = topic.rsplit("/", 1)[-1]

        beacon = (
            models.Beacon.objects.active()
            .filter(
                backend_class_path=constants.BeaconBackendClass.OWNTRACKS,
                pk=identifier,
            )
            .first()
        )

        if not beacon:
            return http.JsonResponse({}, status=404)

        beacon.backend.handle_ping(data)

        return http.JsonResponse({})


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
