import xml.etree.ElementTree as ET

from django.urls import reverse
from django.utils import timezone

import pytest

from bmcc.fields import Coordinate
from bmcc.missions.models import LaunchSite, Mission
from bmcc.tracking import constants
from bmcc.tracking.models import Asset, Beacon, Ping


NS = {"kml": "http://www.opengis.net/kml/2.2"}


def find_folder(parent, name):
    for folder in parent.findall("kml:Folder", NS):
        folder_name = folder.find("kml:name", NS)
        if folder_name is not None and folder_name.text == name:
            return folder
    raise AssertionError(f"Folder named '{name}' not found")


def first_placemark(folder):
    placemark = folder.find("kml:Placemark", NS)
    assert placemark is not None, "Placemark missing"
    return placemark


def placemark_coordinates(placemark, geometry_tag):
    geometry = placemark.find(f"kml:{geometry_tag}", NS)
    assert geometry is not None, f"{geometry_tag} missing on placemark"
    coords_text = geometry.find("kml:coordinates", NS).text.strip()
    return [tuple(c.split(",")) for c in coords_text.split()]


@pytest.mark.django_db()
def test_kml_entrypoint_links_to_update(client):
    mission = Mission.objects.create(name="Test Mission")

    response = client.get(f"/missions/{mission.pk}.kml")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    update_url = reverse(
        "missions:updating_kml", kwargs={"mission_id": mission.pk}
    )
    assert "NetworkLink" in content
    assert f"http://testserver{update_url}" in content
    assert "<refreshMode>onInterval</refreshMode>" in content
    assert "<refreshInterval>10</refreshInterval>" in content


@pytest.mark.django_db()
def test_kml_update_builds_folder_hierarchy_with_tracks_and_positions(client):
    now = timezone.now()
    mission = Mission.objects.create(name="Mission KML")
    LaunchSite.objects.create(
        mission=mission,
        name="Field Alpha",
        location=Coordinate(30.0, 40.0),
        altitude=None,
    )

    balloon = Asset.objects.create(
        mission=mission,
        name="Balloon 1",
        asset_type=constants.AssetType.BALLOON,
    )
    balloon_beacon = Beacon.objects.create(
        asset=balloon,
        identifier="bal-1",
        backend_class_path=constants.BeaconBackendClass.BMCC_API,
    )
    Ping.objects.create(
        mission=mission,
        asset=balloon,
        beacon=balloon_beacon,
        reported_at=now,
        position=Coordinate(1.0, 2.0),
        altitude=100,
    )

    vehicle = Asset.objects.create(
        mission=mission,
        name="Car 1",
        callsign="CAR1",
        asset_type=constants.AssetType.VEHICLE,
    )
    vehicle_beacon = Beacon.objects.create(
        asset=vehicle,
        identifier="car-1",
        backend_class_path=constants.BeaconBackendClass.BMCC_API,
    )
    Ping.objects.create(
        mission=mission,
        asset=vehicle,
        beacon=vehicle_beacon,
        reported_at=now,
        position=Coordinate(10.0, 20.0),
        altitude=None,
    )

    response = client.get(
        reverse("missions:updating_kml", kwargs={"mission_id": mission.pk})
    )

    assert response.status_code == 200
    root = ET.fromstring(response.content)
    document = root.find("kml:Document", NS)
    assert document is not None

    balloon_type = find_folder(document, "Balloon")
    vehicle_type = find_folder(document, "Vehicle")

    # Balloon: altitude present, expect 3D coords for track and point
    balloon_track = find_folder(
        find_folder(balloon_type, "Tracks"), "Balloon 1"
    )
    balloon_track_coords = placemark_coordinates(
        first_placemark(balloon_track), "LineString"
    )
    assert all(len(c) == 3 for c in balloon_track_coords)

    balloon_positions = find_folder(
        find_folder(balloon_type, "Current Positions"), "Balloon 1"
    )
    balloon_point_coords = placemark_coordinates(
        first_placemark(balloon_positions), "Point"
    )
    assert all(len(c) == 3 for c in balloon_point_coords)

    # Vehicle: altitude missing, expect 2D coords for track and point
    vehicle_track = find_folder(find_folder(vehicle_type, "Tracks"), "CAR1")
    vehicle_track_coords = placemark_coordinates(
        first_placemark(vehicle_track), "LineString"
    )
    assert all(len(c) == 2 for c in vehicle_track_coords)

    vehicle_positions = find_folder(
        find_folder(vehicle_type, "Current Positions"), "CAR1"
    )
    vehicle_point_coords = placemark_coordinates(
        first_placemark(vehicle_positions), "Point"
    )
    assert all(len(c) == 2 for c in vehicle_point_coords)

    launch_sites = find_folder(document, "Launch sites")
    field_alpha = find_folder(launch_sites, "Field Alpha")
    launch_point_coords = placemark_coordinates(
        first_placemark(field_alpha), "Point"
    )
    assert all(len(c) == 2 for c in launch_point_coords)
