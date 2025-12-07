from django.contrib.gis.db import models

from bmcc.fields import (
    ConfigurableInstanceField,
    CoordinateField,
    UUIDAutoField,
)
from bmcc.missions.models import LaunchSite, Mission

from . import constants, managers


class Asset(models.Model):
    id = UUIDAutoField()
    mission = models.ForeignKey(
        Mission, related_name="assets", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    callsign = models.CharField(max_length=64, blank=True)
    asset_type = models.CharField(max_length=64, choices=constants.AssetType)
    notes = models.TextField(blank=True)
    launch_site = models.ForeignKey(
        LaunchSite,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )
    launched_at = models.DateTimeField(null=True, blank=True)
    landed_at = models.DateTimeField(null=True, blank=True)
    landing_location = CoordinateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.callsign or self.name

    def __kml__(self):
        from bmcc.utils.kml import E as kml

        return kml.Folder(
            kml.name(self.name),
            *(b.__kml__() for b in self.beacons.all()),
        )

    def clean(self):
        super().clean()
        if self.launch_site and self.launch_site.mission_id != self.mission_id:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                {
                    "launch_site": "Launch site must belong to the asset mission."
                }
            )


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
    backend = ConfigurableInstanceField(
        takes_instance=True, choices=constants.BeaconBackendClass
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = managers.BeaconQuerySet.as_manager()

    class Meta:
        ordering = ["identifier"]

    def __str__(self):
        return self.identifier

    def __kml__(self):
        from bmcc.utils.kml import E as kml

        folder = kml.Folder(
            kml.name(self.identifier),
        )

        pings = list(self.pings.order_by("reported_at").all())
        if not pings:
            return folder

        last_ping = pings[-1]
        coords = [f"{p.longitude},{p.latitude},{p.altitude}" for p in pings]

        visible = False
        if (
            self.asset.asset_type == constants.AssetType.BALLOON
            and last_ping.altitude is not None
        ):
            point = kml.Point(
                kml.altitudeMode("absolute"),
                kml.coordinates(last_ping.position.kml(last_ping.altitude)),
            )
            icon = (
                "http://maps.google.com/mapfiles/kml/paddle/purple-blank.png"
            )
            track = kml.LineString(
                kml.extrude("1"),
                kml.tessellate("1"),
                kml.altitudeMode("absolute"),
                kml.coordinates(" ".join(coords)),
            )
            style = kml.Style(
                kml.LineStyle(
                    kml.color("7f800080"),
                    kml.width("4"),
                ),
                kml.PolyStyle(
                    kml.color("7f800080"),
                ),
            )
            visible = True
        #     ET.SubElement(pm, "visibility").text = "1" if visibility else "0"
        else:
            point = kml.Point(
                kml.altitudeMode("clampToGround"),
                kml.coordinates(last_ping.position.kml()),
            )
            track = kml.LineString(
                kml.altitudeMode("clampToGround"),
                kml.coordinates(" ".join(coords)),
            )
            if self.asset.asset_type == constants.AssetType.BALLOON:
                style = kml.Style(
                    kml.LineStyle(
                        kml.color("7f800080"),
                        kml.width("4"),
                    ),
                    kml.PolyStyle(
                        kml.color("7f800080"),
                    ),
                )
                icon = "http://maps.google.com/mapfiles/kml/paddle/purple-blank.png"
                visible = True
            else:
                style = kml.Style(
                    kml.LineStyle(
                        kml.color("ff000000"),
                        kml.width("4"),
                    ),
                )
                icon = "http://maps.google.com/mapfiles/kml/shapes/woman.png"

        folder.append(
            kml.Placemark(
                kml.name(self.identifier),
                point,
                kml.Style(
                    kml.IconStyle(
                        kml.Icon(
                            kml.href(icon),
                        )
                    )
                ),
            ),
        )
        folder.append(
            kml.Placemark(
                kml.name("Track"),
                track,
                style,
                kml.visibility("1" if visible else "0"),
            ),
        )

        return folder

    def last_ping(self):
        return self.pings.order_by("-reported_at").first()


class Ping(models.Model):
    id = UUIDAutoField()
    # Denormalized mission and asset fields to retain original assignment
    # when a tracker is reused on a different asset/mission
    mission = models.ForeignKey(
        Mission,
        related_name="pings",
        on_delete=models.CASCADE,
    )
    asset = models.ForeignKey(
        Asset,
        related_name="pings",
        on_delete=models.CASCADE,
    )
    beacon = models.ForeignKey(
        Beacon,
        related_name="pings",
        on_delete=models.CASCADE,
    )
    reported_at = models.DateTimeField()
    position = CoordinateField()
    altitude = models.IntegerField(null=True, blank=True)
    accuracy = models.IntegerField(null=True, blank=True)
    speed = models.IntegerField(null=True, blank=True)
    course = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    prediction = models.ForeignKey(
        "predictions.Prediction",
        related_name="pings",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reported_at", "-created_at"]
        indexes = [
            models.Index(fields=["beacon", "reported_at"]),
        ]

    def __str__(self):
        return f"{self.beacon} @ {self.reported_at.isoformat()}"

    @property
    def longitude(self):
        return self.position.longitude

    @property
    def latitude(self):
        return self.position.latitude

    def save(self, *args, **kwargs):
        if self.asset_id is None:
            self.asset = self.beacon.asset
        if self.mission_id is None:
            self.mission = self.asset.mission
        super().save(*args, **kwargs)
