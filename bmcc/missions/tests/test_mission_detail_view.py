from django.urls import reverse
from django.utils import timezone

import pytest

from bmcc.fields import Coordinate
from bmcc.missions.models import Mission
from bmcc.tracking import constants
from bmcc.tracking.models import Asset, Beacon, Ping


@pytest.mark.django_db()
def test_mission_detail_renders_assets_and_last_ping(client):
    now = timezone.now()
    mission = Mission.objects.create(
        name="Detail Mission", description="Mission overview page"
    )
    asset = Asset.objects.create(
        mission=mission,
        name="Balloon A",
        asset_type=constants.AssetType.BALLOON,
    )
    beacon = Beacon.objects.create(
        asset=asset,
        identifier="bal-a",
        backend_class_path=constants.BeaconBackendClass.BMCC_API,
        description="Balloon tracker",
    )
    Ping.objects.create(
        mission=mission,
        asset=asset,
        beacon=beacon,
        reported_at=now - timezone.timedelta(minutes=5),
        position=Coordinate(10.1, 20.2),
    )
    latest = Ping.objects.create(
        mission=mission,
        asset=asset,
        beacon=beacon,
        reported_at=now,
        position=Coordinate(33.33333, 44.44444),
        altitude=250,
    )

    response = client.get(
        reverse("missions:detail", kwargs={"mission_id": mission.pk})
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Detail Mission" in content
    assert "Balloon A" in content
    assert "bal-a" in content
    assert "Balloon tracker" in content
    timestamp = timezone.localtime(latest.reported_at).strftime(
        "%Y-%m-%d %H:%M"
    )
    assert timestamp in content
    assert "44.44444" in content
    assert "10.10000" not in content


@pytest.mark.django_db()
def test_mission_get_absolute_url_points_to_detail():
    mission = Mission.objects.create(name="Absolute URL Mission")

    assert mission.get_absolute_url() == reverse(
        "missions:detail", kwargs={"mission_id": mission.pk}
    )
