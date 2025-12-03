from django.contrib import admin
from django.utils import timezone

from adminutils import ModelAdmin, admin_detail_link
from import_export import resources
from import_export.admin import ExportMixin

from . import models


@admin.register(models.Asset)
class AssetAdmin(ModelAdmin):
    list_filter = [
        "mission",
        "asset_type",
    ]
    list_display = [
        "name",
        "callsign",
        "asset_type",
        "mission",
    ]


@admin.register(models.Beacon)
class BeaconAdmin(ModelAdmin):
    search_fields = [
        "identifier",
    ]
    list_display = [
        "identifier",
        "asset",
        "active",
        "last_ping_timestamp",
        "backend_class_path",
        "asset__mission",
    ]
    list_filter = [
        "asset__mission",
        "asset",
        "backend_class_path",
    ]

    def last_ping_timestamp(self, obj):
        ping = obj.last_ping()
        return (
            admin_detail_link(ping, timezone.localtime(ping.reported_at))
            if ping
            else None
        )


class PingResource(resources.ModelResource):
    beacon_identifier = resources.Field()
    beacon_backend = resources.Field()
    asset_name = resources.Field()
    mission_name = resources.Field()
    latitude = resources.Field()
    longitude = resources.Field()

    class Meta:
        model = models.Ping
        fields = (
            "id",
            "reported_at",
            "mission",
            "mission_name",
            "asset",
            "asset_name",
            "beacon",
            "beacon_identifier",
            "beacon_backend",
            "latitude",
            "longitude",
            "altitude",
            "accuracy",
            "speed",
            "course",
            "metadata",
        )
        export_order = fields

    def dehydrate_beacon_identifier(self, obj):
        return obj.beacon.identifier

    def dehydrate_beacon_backend(self, obj):
        return obj.beacon.get_backend_class_path_display()

    def dehydrate_asset_name(self, obj):
        return obj.asset.name

    def dehydrate_mission_name(self, obj):
        return obj.mission.name

    def dehydrate_latitude(self, obj):
        return obj.latitude

    def dehydrate_longitude(self, obj):
        return obj.longitude


@admin.register(models.Ping)
class PingAdmin(ExportMixin, ModelAdmin):
    date_hierarchy = "reported_at"
    list_display = [
        "reported_at",
        "beacon",
        "asset",
        "mission",
        "altitude",
    ]
    list_filter = [
        "mission",
        "asset",
        "beacon",
    ]
    resource_class = PingResource
