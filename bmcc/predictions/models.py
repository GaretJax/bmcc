from django.contrib.gis.db import models as gis_models
from django.db import models

from bmcc.fields import UUIDAutoField


class Prediction(models.Model):
    id = UUIDAutoField()

    launch_at = models.DateTimeField()
    launch_location = gis_models.PointField(geography=True, dim=3)

    bursting_at = models.DateTimeField(null=True, blank=True)
    burst_location = gis_models.PointField(
        geography=True, dim=3, null=True, blank=True
    )

    landing_at = models.DateTimeField(null=True, blank=True)
    landing_location = gis_models.PointField(
        geography=True, dim=3, null=True, blank=True
    )

    prediction = models.JSONField(null=True, blank=True)

    additional_parameters = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-launch_at"]

    def __str__(self):
        return f"Prediction @ {self.launch_at.isoformat()}"
