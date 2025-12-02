from datetime import UTC, datetime
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis.geos import Point
from django.urls import reverse

import attrs

from .. import models


@attrs.frozen()
class OwnTracksBackend:
    beacon: models.Beacon

    def handle_ping(self, data):
        self.beacon.pings.create(
            position=Point(data["lon"], data["lat"]),
            altitude=data.get("alt", None),
            accuracy=data.get("acc", None),
            speed=data.get("vel", None),
            reported_at=datetime.fromtimestamp(data["tst"], tz=UTC),
            metadata=data,
        )

        # https://owntracks.org/booklet/tech/json/
        # {
        #     "p": 101.338,
        #     "tid": "B4",
        #     "vac": 30,
        #     "_type": "location",
        #     "topic": "owntracks/user/0C3CB2B9-641A-4BDD-8A80-61A675FC29B4",
        #     "created_at": 1763869517,
        # }

    def get_config(self):
        return {
            "_type": "configuration",
            "info": f"OwnTracks setup for {self.beacon.asset.name}",
            "connection": "bmcc",
            "connections": {
                "bmcc": {
                    "type": "http",
                    "url": urljoin(
                        settings.BASE_URL, reverse("tracking:owntracks_ping")
                    ),
                    "deviceId": str(self.beacon.identifier)[:2],
                    "trackerId": str(self.beacon.pk),
                    "auth": False,
                }
            },
        }
