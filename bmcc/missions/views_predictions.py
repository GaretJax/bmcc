from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from bmcc.fields import Coordinate
from bmcc.predictions.models import Prediction
from bmcc.predictions.tasks import run_prediction

from .models import LaunchSite, Mission


@require_POST
def run_launch_site_prediction(request, mission_id, launch_site_id):
    mission = get_object_or_404(Mission, pk=mission_id)
    launch_site = get_object_or_404(
        LaunchSite, pk=launch_site_id, mission=mission
    )
    ascent = mission.ascent_rate
    burst = mission.burst_altitude
    descent = mission.descent_rate
    if ascent is None or burst is None or descent is None:
        return redirect(
            "missions:launch_site_detail",
            mission_id=mission.pk,
            launch_site_id=launch_site.pk,
        )

    prediction = Prediction.objects.create(
        launch_at=launch_site.intended_launch_at or timezone.now(),
        launch_location=Coordinate(
            launch_site.location.x,
            launch_site.location.y,
        ),
        launch_altitude=launch_site.altitude,
        additional_parameters={
            "ascent_rate": ascent,
            "burst_altitude": burst,
            "descent_rate": descent,
        },
    )
    launch_site.prediction_history.add(prediction)
    run_prediction.delay(prediction.pk)
    return redirect(
        "missions:launch_site_detail",
        mission_id=mission.pk,
        launch_site_id=launch_site.pk,
    )
