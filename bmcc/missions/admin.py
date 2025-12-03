from django.contrib import admin

from adminutils import ModelAdmin

from . import models


@admin.register(models.Mission)
class MissionAdmin(ModelAdmin):
    pass


@admin.register(models.LaunchSiteCandidate)
class LaunchSiteCandidateAdmin(ModelAdmin):
    list_display = [
        "name",
        "mission",
        "intended_launch_at",
    ]
    list_filter = [
        "mission",
    ]
    search_fields = ["name", "mission__name"]
