from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.urls import reverse

from bmcc.fields import CoordinateField, UUIDAutoField


class Mission(models.Model):
    id = UUIDAutoField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ascent_rate = models.FloatField(null=True, blank=True)
    burst_altitude = models.FloatField(null=True, blank=True)
    descent_rate = models.FloatField(null=True, blank=True)
    mission_window = DateTimeRangeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def __kml__(self, parent):
        pass

    def get_absolute_url(self):
        return reverse("missions:detail", kwargs={"mission_id": self.pk})


class LaunchSite(models.Model):
    id = UUIDAutoField()
    mission = models.ForeignKey(
        Mission,
        related_name="launch_site_candidates",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    location = CoordinateField()
    altitude = models.FloatField(null=True, blank=True)
    intended_launch_at = models.DateTimeField(
        null=True, blank=True, help_text="Planned datetime for launch"
    )
    prediction = models.ForeignKey(
        "predictions.Prediction",
        related_name="launch_site_candidates",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    prediction_history = models.ManyToManyField(
        "predictions.Prediction",
        related_name="launch_site_history",
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["mission", "name"]

    def __str__(self):
        return f"{self.name} ({self.mission})"

    def __kml__(self):
        from bmcc.utils.kml import E as kml

        folder = kml.Folder(
            kml.name(self.name),
            kml.Placemark(
                kml.name("Launch location"),
                kml.Point(
                    kml.altitudeMode("absolute"),
                    kml.coordinates(self.location.kml(altitude=self.altitude)),
                ),
            ),
        )
        predictions = kml.Folder(kml.name("Predictions"))
        folder.append(predictions)
        for prediction in self.prediction_history.filter(
            prediction__isnull=False
        ):
            predictions.append(prediction.__kml__())

        return folder
