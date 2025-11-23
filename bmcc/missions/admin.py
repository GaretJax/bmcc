from django.contrib import admin

from adminutils import ModelAdmin

from . import models


@admin.register(models.Mission)
class MissionAdmin(ModelAdmin):
    pass
