import base64
import json

from django import http
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, FormView

from bmcc.missions.models import Mission

from . import constants, forms, models


@method_decorator(csrf_exempt, name="dispatch")
class OwnTracksPingView(View):
    def post(self, request, *args, **kwargs):
        beacon = (
            models.Beacon.objects.active()
            .filter(backend_class_path=constants.BeaconBackendClass.OWNTRACKS)
            .first()
        )

        if beacon:
            beacon.backend.handle_ping(beacon, json.loads(request.body))

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
        context.update(
            {
                "beacon": self.beacon,
                "asset": self.beacon.asset,
                "tracker_id": self.get_tracker_id(),
            }
        )
        return context


class OwnTracksRegisterView(MissionContextMixin, FormView):
    form_class = forms.OwnTracksRegistrationForm
    template_name = "tracking/owntracks_register.html"

    def form_valid(self, form):
        _, self.created_beacon = form.create_objects(self.mission)
        return redirect(
            "tracking:owntracks_configuration",
            beacon_id=self.created_beacon.id,
        )


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
