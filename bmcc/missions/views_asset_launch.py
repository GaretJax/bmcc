from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..tracking.models import Asset
from .models import LaunchSite, Mission


@require_POST
def asset_mark_launched(request, mission_id, asset_id):
    mission = get_object_or_404(Mission, pk=mission_id)
    asset = get_object_or_404(Asset, pk=asset_id, mission=mission)

    launch_site_id = request.POST.get("launch_site")
    launched_at = request.POST.get("launched_at")

    launch_site = None
    if launch_site_id:
        launch_site = LaunchSite.objects.filter(
            pk=launch_site_id, mission=mission
        ).first()

    parsed_launched_at = None
    if launched_at:
        try:
            parsed_launched_at = timezone.datetime.fromisoformat(launched_at)
            if timezone.is_naive(parsed_launched_at):
                parsed_launched_at = timezone.make_aware(
                    parsed_launched_at, timezone.get_current_timezone()
                )
        except ValueError:
            parsed_launched_at = timezone.now()
    else:
        parsed_launched_at = timezone.now()

    asset.launch_site = launch_site
    asset.launched_at = parsed_launched_at
    asset.save(update_fields=["launch_site", "launched_at"])
    return redirect(
        "missions:asset_detail", mission_id=mission.pk, asset_id=asset.pk
    )
