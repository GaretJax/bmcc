from django.contrib import admin

from adminutils import ModelAdmin

from . import models


@admin.register(models.Asset)
class AssetAdmin(ModelAdmin):
    pass


@admin.register(models.Beacon)
class BeaconAdmin(ModelAdmin):
    pass


@admin.register(models.Ping)
class PingAdmin(ModelAdmin):
    pass
