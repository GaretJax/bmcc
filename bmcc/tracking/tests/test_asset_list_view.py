from django.urls import reverse
from django.utils import timezone

import pytest

from bmcc.fields import Coordinate
from bmcc.missions.models import Mission
from bmcc.tracking import constants
from bmcc.tracking.models import Asset, Beacon, Ping


@pytest.mark.django_db()
def test_asset_list_shows_latest_ping(client):
    now = timezone.now()
    mission = Mission.objects.create(name="Mission A")
    asset = Asset.objects.create(
        mission=mission,
        name="Vehicle 1",
        asset_type=constants.AssetType.VEHICLE,
    )
    beacon = Beacon.objects.create(
        asset=asset,
        identifier="veh-1",
        backend_class_path=constants.BeaconBackendClass.BMCC_API,
    )
    Ping.objects.create(
        mission=mission,
        asset=asset,
        beacon=beacon,
        reported_at=now - timezone.timedelta(minutes=5),
        position=Coordinate(1.0, 2.0),
        altitude=100,
    )
    latest = Ping.objects.create(
        mission=mission,
        asset=asset,
        beacon=beacon,
        reported_at=now,
        position=Coordinate(3.33333, 4.44444),
        altitude=150,
    )

    response = client.get(
        reverse("missions:asset_list", kwargs={"mission_id": mission.pk})
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Vehicle 1" in content
    timestamp = timezone.localtime(latest.reported_at).strftime(
        "%Y-%m-%d %H:%M"
    )
    assert timestamp in content
    assert "4.44444" in content
    assert "2.00000" not in content
    assert "150" in content
    assert "veh-1" in content
