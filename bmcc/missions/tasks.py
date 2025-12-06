import logging

from django.utils import timezone

from celery import shared_task

from bmcc.predictions.backends.tawhiri import TawhiriBackend
from bmcc.predictions.models import Prediction

from .models import LaunchSite


logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True)
def generate_predictions_for_future_launches(self):
    now = timezone.now()
    backend = TawhiriBackend()
    created = 0
    updated = 0

    candidates = (
        LaunchSite.objects.select_related("mission")
        .filter(intended_launch_at__gt=now)
        .order_by("mission_id", "intended_launch_at")
    )

    for site in candidates.iterator():
        additional_params = dict(site.metadata or {})
        mission = site.mission
        if mission.ascent_rate is not None:
            additional_params.setdefault("ascent_rate", mission.ascent_rate)
        if mission.burst_altitude is not None:
            additional_params.setdefault(
                "burst_altitude", mission.burst_altitude
            )
        if mission.descent_rate is not None:
            additional_params.setdefault("descent_rate", mission.descent_rate)
        additional_params.setdefault("profile", "standard_profile")
        additional_params.setdefault("pred_type", "single")

        missing = [
            key
            for key in ("ascent_rate", "burst_altitude", "descent_rate")
            if additional_params.get(key) is None
        ]
        if missing or not site.intended_launch_at:
            logger.warning(
                "Skipping launch site prediction due to missing parameters",
                extra={
                    "launch_site_id": str(site.id),
                    "mission_id": str(site.mission_id),
                    "missing": missing,
                    "has_launch_time": bool(site.intended_launch_at),
                },
            )
            continue

        prediction = Prediction.objects.create(
            launch_at=site.intended_launch_at,
            launch_location=site.location,
            launch_altitude=site.altitude,
            additional_parameters=additional_params,
        )
        site.prediction_history.add(prediction)
        created += 1

        try:
            backend.run(prediction)
        except Exception:
            logger.exception(
                "Tawhiri prediction failed",
                extra={
                    "prediction_id": str(prediction.id),
                    "launch_site_id": str(site.id),
                    "mission_id": str(site.mission_id),
                },
            )
            continue

        site.prediction = prediction
        site.save(update_fields=["prediction"])
        updated += 1

    logger.info(
        "Launch site prediction generation complete",
        extra={
            "created_at": created,
            "updated_at": updated,
            "candidate_count": len(candidates),
        },
    )
    return {"created": created, "updated": updated}
