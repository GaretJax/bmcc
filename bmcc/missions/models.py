from django.contrib.gis.db import models as gis_models
from django.db import models

from bmcc.fields import UUIDAutoField


class Mission(models.Model):
    id = UUIDAutoField()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ascent_rate = models.FloatField(null=True, blank=True)
    burst_altitude = models.FloatField(null=True, blank=True)
    descent_rate = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LaunchSiteCandidate(models.Model):
    id = UUIDAutoField()
    mission = models.ForeignKey(
        Mission,
        related_name="launch_site_candidates",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    location = gis_models.PointField(geography=True, dim=2)
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
