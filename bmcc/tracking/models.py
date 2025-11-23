from django.contrib.gis.db import models

from bmcc.fields import ConfigurableInstanceField, UUIDAutoField
from bmcc.missions.models import Mission

from . import constants


class Asset(models.Model):
    id = UUIDAutoField()
    mission = models.ForeignKey(
        Mission, related_name="assets", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    callsign = models.CharField(max_length=64, blank=True)
    asset_type = models.CharField(max_length=64, choices=constants.AssetType)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.callsign or self.name


class Beacon(models.Model):
    id = UUIDAutoField()
    asset = models.ForeignKey(
        Asset,
        related_name="beacons",
        on_delete=models.CASCADE,
    )
    identifier = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    backend = ConfigurableInstanceField(choices=constants.BeaconBackendClass)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["identifier"]

    def __str__(self):
        return self.identifier


class Ping(models.Model):
    id = UUIDAutoField()
    beacon = models.ForeignKey(
        Beacon,
        related_name="pings",
        on_delete=models.CASCADE,
    )
    reported_at = models.DateTimeField()
    position = models.PointField(geography=True)
    speed = models.FloatField(null=True, blank=True)
    course = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reported_at", "-created_at"]
        indexes = [
            models.Index(fields=["beacon", "reported_at"]),
        ]

    def __str__(self):
        return f"{self.beacon} @ {self.reported_at.isoformat()}"
