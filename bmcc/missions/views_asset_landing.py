from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from bmcc.fields import Coordinate

from ..tracking.models import Asset
from .models import Mission


@require_POST
def asset_mark_landed(request, mission_id, asset_id):
    mission = get_object_or_404(Mission, pk=mission_id)
    asset = get_object_or_404(Asset, pk=asset_id, mission=mission)

    lat = request.POST.get("latitude")
    lon = request.POST.get("longitude")
    landed_at = request.POST.get("landed_at")

    parsed_landed_at = None
    if landed_at:
        try:
            parsed_landed_at = timezone.datetime.fromisoformat(landed_at)
            if timezone.is_naive(parsed_landed_at):
                parsed_landed_at = timezone.make_aware(
                    parsed_landed_at, timezone.get_current_timezone()
                )
        except ValueError:
            parsed_landed_at = timezone.now()
    else:
        parsed_landed_at = timezone.now()

    location = None
    if lat and lon:
        try:
            location = Coordinate(float(lon), float(lat))
        except (TypeError, ValueError):
            location = None

    asset.landed_at = parsed_landed_at
    asset.landing_location = location
    asset.save(update_fields=["landed_at", "landing_location"])
    return redirect(
        "missions:asset_detail", mission_id=mission.pk, asset_id=asset.pk
    )
