from django.db import models
from django.utils.translation import gettext_lazy as _


class BeaconBackendClass(models.TextChoices):
    BMCC_API = ("bmcc.tracking.backends.bmcc_api.ApiBackend", _("BMCC API"))
    OWNTRACKS = ("bmcc.tracking.backends.owntracks.OwnTracks", _("OwnTracks"))
    SPOT = ("bmcc.tracking.backends.spot.SpotBackend", _("SPOT"))


class AssetType(models.TextChoices):
    BALLOON = ("balloon", _("Balloon"))
    VEHICLE = ("vehicle", _("Vehicle"))
