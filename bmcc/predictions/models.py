from django.db import models

from bmcc.fields import CoordinateField, UUIDAutoField


class Prediction(models.Model):
    id = UUIDAutoField()

    launch_at = models.DateTimeField()
    launch_location = CoordinateField()
    launch_altitude = models.FloatField(null=True, blank=True)

    bursting_at = models.DateTimeField(null=True, blank=True)
    burst_location = CoordinateField(null=True, blank=True)
    burst_altitude = models.FloatField(null=True, blank=True)

    landing_at = models.DateTimeField(null=True, blank=True)
    landing_location = CoordinateField(null=True, blank=True)
    landing_altitude = models.FloatField(null=True, blank=True)

    prediction = models.JSONField(null=True, blank=True)

    additional_parameters = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-launch_at"]

    def __str__(self):
        return f"Prediction @ {self.launch_at.isoformat()}"

    def __kml__(self):
        from bmcc.utils.kml import E as kml

        coords = [
            f"{c['longitude']},{c['latitude']},{c['altitude']}"
            for c in (
                self.prediction["prediction"][0]["trajectory"]
                + self.prediction["prediction"][1]["trajectory"]
            )
        ]

        return kml.Folder(
            kml.name(self.created_at.isoformat()),
            kml.Placemark(
                kml.name("Trajectory"),
                kml.description(
                    f"Ascent rate: {self.additional_parameters['ascent_rate']}m/s, "
                    f"descent rate: {self.additional_parameters['descent_rate']}m/s, "
                    f"burst at: {self.burst_altitude:.0f}m"
                ),
                kml.LineString(
                    kml.extrude("1"),
                    kml.tessellate("1"),
                    kml.altitudeMode("absolute"),
                    kml.coordinates(" ".join(coords)),
                ),
                kml.Style(
                    kml.LineStyle(
                        kml.color("7f00ffff"),
                        kml.width("4"),
                    ),
                    kml.PolyStyle(
                        kml.color("7f00ff00"),
                    ),
                ),
            ),
            kml.Placemark(
                kml.name("Burst"),
                kml.description(
                    f"Burst at {self.burst_location}, "
                    f"{self.burst_altitude:.0f}m, "
                    f"at {self.bursting_at.isoformat()}"
                ),
                kml.Point(
                    kml.altitudeMode("absolute"),
                    kml.coordinates(
                        self.burst_location.kml(altitude=self.burst_altitude)
                    ),
                ),
            ),
            kml.Placemark(
                kml.name("Landing"),
                kml.description(
                    f"Landing at {self.landing_location}, "
                    f"{self.landing_altitude:.0f}m, "
                    f"at {self.landing_at.isoformat()}"
                ),
                kml.Point(
                    kml.altitudeMode("absolute"),
                    kml.coordinates(
                        self.landing_location.kml(
                            altitude=self.landing_altitude
                        )
                    ),
                ),
            ),
        )

    @property
    def ascent_duration(self):
        return self.bursting_at - self.launch_at
