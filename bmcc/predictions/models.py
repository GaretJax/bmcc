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

    @property
    def ascent_duration(self):
        return self.bursting_at - self.launch_at
