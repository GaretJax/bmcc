import enum
import logging
from datetime import datetime

from django.conf import settings

import attrs
import requests

from bmcc.fields import Coordinate

from .. import models


SPOT_API_URL = "https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/{feed_id}/message.json"


class MessageType(enum.StrEnum):
    TRACK = "TRACK"


logger = logging.getLogger(__name__)


@attrs.frozen
class SpotBackend:
    beacon: models.Beacon
    device_id: str

    @staticmethod
    def retrieve_messages():
        url = SPOT_API_URL.format(feed_id=settings.SPOT_FEED_ID)
        response = requests.get(url)
        response.raise_for_status()
        payload = response.json()
        return payload["response"]["feedMessageResponse"]["messages"][
            "message"
        ]

    def process_messages(self, messages: list):
        for message in messages:
            if message["messengerId"] == self.device_id:
                if message["messageType"] != MessageType.TRACK:
                    logging.error(
                        "Unknown message type: %s", message["messageType"]
                    )
                    continue
                reported_at = datetime.fromisoformat(message["dateTime"])
                position = Coordinate(
                    message["longitude"], message["latitude"]
                )
                # altitude = message["altitude"]
                ping, created = self.beacon.pings.get_or_create(
                    beacon=self.beacon,
                    reported_at=reported_at,
                    defaults={
                        "mission": self.beacon.asset.mission,
                        "asset": self.beacon.asset,
                        "position": position,
                        # "altitude": altitude,  # Not supported on SPOT 2
                        "metadata": message,
                    },
                )
