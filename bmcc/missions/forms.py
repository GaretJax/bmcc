import logging

from django import forms
from django.contrib.gis.geos import Point

import requests

from .models import LaunchSite, Mission


logger = logging.getLogger(__name__)


class LaunchSiteForm(forms.ModelForm):
    latitude = forms.FloatField()
    longitude = forms.FloatField()

    class Meta:
        model = LaunchSite
        fields = ["name", "intended_launch_at"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.location = Point(
            self.cleaned_data["longitude"], self.cleaned_data["latitude"]
        )
        if obj.altitude in (None, ""):
            try:
                resp = requests.get(
                    "https://epqs.nationalmap.gov/v1/json",
                    params={
                        "x": obj.location.x,
                        "y": obj.location.y,
                        "units": "meters",
                        "wkid": 4326,
                    },
                    timeout=5,
                )
                if resp.ok:
                    data = resp.json()
                    value = (
                        data.get("value")
                        or data.get("elevation")
                        or data.get("data", {}).get("elevation")
                    )
                    if value is not None:
                        obj.altitude = float(value)
                else:
                    logger.warning(
                        "EPQS lookup failed",
                        extra={"status": resp.status_code, "url": resp.url},
                    )
            except Exception:
                logger.exception(
                    "EPQS lookup error",
                    extra={
                        "longitude": obj.location.x,
                        "latitude": obj.location.y,
                    },
                )
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class MissionParametersForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ["ascent_rate", "burst_altitude", "descent_rate"]
        labels = {
            "ascent_rate": "Ascent speed (m/s)",
            "burst_altitude": "Target burst altitude (m)",
            "descent_rate": "Descent speed (m/s)",
        }
        widgets = {
            "ascent_rate": forms.NumberInput(attrs={"step": "0.1"}),
            "burst_altitude": forms.NumberInput(attrs={"step": "1"}),
            "descent_rate": forms.NumberInput(attrs={"step": "0.1"}),
        }


class LaunchSiteUpdateForm(forms.ModelForm):
    class Meta:
        model = LaunchSite
        fields = ["intended_launch_at"]
