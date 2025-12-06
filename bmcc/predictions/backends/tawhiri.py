import logging
from typing import Any

from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.dateparse import parse_datetime

import requests

from bmcc.predictions.models import Prediction


logger = logging.getLogger(__name__)


class TawhiriBackend:
    """
    Tawhiri API v2 client.
    Reference payload/response inferred from:
    https://api.v2.sondehub.org/tawhiri
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or getattr(
            settings,
            "TAWHIRI_API_URL",
            "https://api.v2.sondehub.org/tawhiri",
        )

    def run(self, prediction: Prediction) -> Prediction:
        params = self._build_params(prediction)
        logger.info(
            "Submitting Tawhiri v2 prediction",
            extra={
                "prediction_id": str(prediction.id),
                "launch_at": prediction.launch_at.isoformat(),
                "endpoint": self.base_url,
            },
        )

        response = requests.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        self._apply_results(prediction, data)
        prediction.save(
            update_fields=[
                "bursting_at",
                "burst_location",
                "burst_altitude",
                "landing_at",
                "landing_location",
                "landing_altitude",
                "prediction",
                "updated_at",
            ]
        )
        return prediction

    def _build_params(self, prediction: Prediction) -> dict[str, Any]:
        """
        Build query parameters for Tawhiri v2 API.
        Additional parameters (e.g., profile, ascent_rate) can be provided
        via prediction.additional_parameters.
        """
        lon = prediction.launch_location.x
        if lon < 0:
            lon = 360 + lon
        params = {
            "launch_latitude": prediction.launch_location.y,
            "launch_longitude": lon,
            "launch_altitude": prediction.launch_altitude or 0,
            "launch_datetime": prediction.launch_at.isoformat(),
        }
        params.update(prediction.additional_parameters or {})
        return params

    def _apply_results(self, prediction: Prediction, data: dict[str, Any]):
        prediction.prediction = data

        ascent, descent = data["prediction"]
        burst = ascent["trajectory"][-1]
        land = descent["trajectory"][-1]

        prediction.bursting_at = parse_datetime(burst["datetime"])
        prediction.burst_location = Point(
            burst["longitude"],
            burst["latitude"],
        )
        prediction.burst_altitude = burst["altitude"]

        prediction.landing_at = parse_datetime(land["datetime"])
        prediction.land_location = Point(
            land["longitude"],
            land["latitude"],
        )
        prediction.land_altitude = land["altitude"]
