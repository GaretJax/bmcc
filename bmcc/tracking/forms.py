from django import forms

from . import constants, models


class OwnTracksRegistrationForm(forms.Form):
    asset_name = forms.CharField(label="Asset name", max_length=255)
    beacon_identifier = forms.CharField(
        label="Beacon identifier",
        max_length=128,
        help_text="Unique identifier for this device",
    )

    def clean_beacon_identifier(self):
        identifier = self.cleaned_data["beacon_identifier"].strip()
        if models.Beacon.objects.filter(identifier=identifier).exists():
            raise forms.ValidationError(
                "A beacon with this identifier already exists."
            )
        return identifier

    def create_objects(self, mission):
        asset = models.Asset.objects.create(
            mission=mission,
            name=self.cleaned_data["asset_name"],
            asset_type=constants.AssetType.VEHICLE,
        )
        beacon = models.Beacon.objects.create(
            asset=asset,
            identifier=self.cleaned_data["beacon_identifier"],
            backend_class_path=constants.BeaconBackendClass.OWNTRACKS,
        )
        return asset, beacon
