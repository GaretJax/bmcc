from celery import shared_task

from . import constants, models
from .backends.spot import SpotBackend


@shared_task
def update_beacon_locations_spot():
    beacons = models.Beacon.objects.active().filter(
        backend_class_path=constants.BeaconBackendClass.SPOT
    )

    if not beacons:
        return

    messages = SpotBackend.retrieve_messages()
    for beacon in beacons.iterator():
        beacon.backend.process_messages(messages)
