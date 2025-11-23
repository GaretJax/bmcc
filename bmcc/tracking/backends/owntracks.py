from django.contrib.gis.geos import Point
from django.utils import timezone


class OwnTracksBackend:
    def handle_ping(self, beacon, data):
        beacon.pings.create(
            reported_at=timezone.now(),
            position=Point(0, 0),
            altitude=0,
            metadata=data,
        )
