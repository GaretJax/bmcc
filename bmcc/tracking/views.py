import json
from urllib.parse import quote

from django import http
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView

from bmcc.missions.models import Mission

from . import constants, forms, models


@method_decorator(csrf_exempt, name="dispatch")
class OwnTracksPingView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        identifier = data.get("device")
        if not identifier:
            topic = data.get("topic", "")
            if topic:
                identifier = topic.rsplit("/", 1)[-1]

        beacon = (
            models.Beacon.objects.active()
            .filter(
                backend_class_path=constants.BeaconBackendClass.OWNTRACKS,
                identifier=identifier,
            )
            .first()
        )

        if beacon:
            beacon.backend.handle_ping(data)

        return http.HttpResponse()


class MissionContextMixin:
    mission = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.mission = get_object_or_404(Mission, pk=kwargs.get("mission_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mission"] = self.mission
        return context


class BeaconMissionMixin(MissionContextMixin):
    beacon = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.beacon = get_object_or_404(
            models.Beacon.objects.select_related("asset__mission"),
            pk=kwargs.get("beacon_id"),
            asset__mission=self.mission,
        )

    def get_tracker_id(self):
        tracker_id = self.beacon.identifier[:2].upper()
        if len(tracker_id) == 1:
            tracker_id = tracker_id + tracker_id
        return tracker_id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "beacon": self.beacon,
            "asset": self.beacon.asset,
            "tracker_id": self.get_tracker_id(),
        })
        return context


class OwnTracksRegisterView(MissionContextMixin, FormView):
    form_class = forms.OwnTracksRegistrationForm
    template_name = "tracking/owntracks_register.html"

    def form_valid(self, form):
        _, self.created_beacon = form.create_objects(self.mission)
        return redirect(
            "tracking:owntracks_configuration",
            mission_id=self.mission.id,
            beacon_id=self.created_beacon.id,
        )


class OwnTracksConfigurationView(BeaconMissionMixin, TemplateView):
    template_name = "tracking/owntracks_configuration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config_url = self.request.build_absolute_uri(
            reverse(
                "tracking:owntracks_configuration_file",
                kwargs={"mission_id": self.mission.id, "beacon_id": self.beacon.id},
            )
        )
        report_url = self.request.build_absolute_uri(reverse("tracking:owntracks_ping"))
        remote_config_link = f"owntracks:///config?url={quote(config_url)}"

        context.update(
            {
                "remote_config_link": remote_config_link,
                "configuration_url": config_url,
                "report_url": report_url,
            }
        )
        return context


class OwnTracksConfigurationFileView(BeaconMissionMixin, View):
    def get(self, request, *args, **kwargs):
        payload = {
            "_type": "configuration",
            "info": f"OwnTracks setup for {self.beacon.asset.name}",
            "connection": "bmcc",
            "connections": {
                "bmcc": {
                    "type": "http",
                    "url": request.build_absolute_uri(reverse("tracking:owntracks_ping")),
                    "deviceId": str(self.beacon.identifier),
                    "trackerId": self.get_tracker_id(),
                    "auth": False,
                }
            },
        }

        return http.JsonResponse(payload)
