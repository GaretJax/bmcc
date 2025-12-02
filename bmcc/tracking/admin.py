from django.contrib import admin

from adminutils import ModelAdmin, admin_detail_link

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
        return admin_detail_link(ping, ping.reported_at)


@admin.register(models.Ping)
class PingAdmin(ModelAdmin):
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
