from datetime import UTC, datetime
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

import attrs

from bmcc.fields import Coordinate

from .. import models


@attrs.frozen()
class OwnTracksBackend:
    beacon: models.Beacon
    show_all: bool = False

    def handle_ping(self, data):
        if data["_type"] != "location":
            raise ValueError("Not a location message")

        ping = self.beacon.pings.create(
            position=Coordinate(data["lon"], data["lat"]),
            altitude=data.get("alt", None),
            accuracy=data.get("acc", None),
            speed=data.get("vel", None),
            reported_at=datetime.fromtimestamp(data["tst"], tz=UTC),
            metadata=data,
        )

        pending = list(
            self.beacon.owntracks_messages.filter(sent_at__isnull=True)
        )
        now = timezone.now()
        outbound = []
        if pending:
            for msg in pending:
                outbound.append(msg.message)
                msg.sent_at = now
            models.OwnTracksMessage.objects.bulk_update(pending, ["sent_at"])

        if not self.show_all:
            return ping, outbound

        friends = (
            models.Beacon.objects.active()
            .filter(
                asset__mission_id=self.beacon.asset.mission_id,
                pings__isnull=False,
            )
            .exclude(pk=self.beacon.pk)
        )
        return ping, (
            outbound
            + [
                {"_type": "cmd", "action": "clearWaypoints"},
            ]
            + [self.prepare_card_message(beacon) for beacon in friends]
            + [
                self.prepare_location_message(beacon.last_ping())
                for beacon in friends
            ]
        )

        # https://owntracks.org/booklet/tech/json/
        # {
        #     "p": 101.338,
        #     "vac": 30,
        #     "topic": "owntracks/user/0C3CB2B9-641A-4BDD-8A80-61A675FC29B4",
        #     "created_at": 1763869517,
        # }

    def prepare_location_message(self, ping):
        msg = {
            "_type": "location",
            "lon": ping.longitude,
            "lat": ping.latitude,
            "tid": ping.beacon.identifier[:2],
            "deviceId": str(ping.beacon.pk),
            "tst": ping.reported_at.timestamp(),
        }
        if ping.altitude is not None:
            msg["alt"] = ping.altitude
        if ping.accuracy is not None:
            msg["acc"] = ping.accuracy
        if ping.speed is not None:
            msg["speed"] = ping.speed

        return msg

    def prepare_card_message(self, beacon):
        return {
            "_type": "card",
            "tid": beacon.identifier[:2],
            "name": beacon.asset.name,
        }

    def get_config(self):
        return {
            "_type": "configuration",
            "deviceId": str(self.beacon.pk),
            "tid": self.beacon.identifier[:2],
            "days": 1,
            "mode": 3,
            "url": urljoin(
                settings.BASE_URL, reverse("tracking:owntracks_ping")
            ),
            "auth": False,
            "remoteConfiguration": True,
        }
