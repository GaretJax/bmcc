from datetime import UTC, datetime

from django.contrib.gis.geos import Point

from .. import models


class OwnTracksBackend:
    beacon: models.Beacon

    def __init__(self, beacon):
        self.beacon = beacon

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
