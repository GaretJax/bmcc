from django.contrib import admin

from adminutils import ModelAdmin

from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(ModelAdmin):
    list_display = [
        "launch_at",
        "bursting_at",
        "landing_at",
        "created_at",
    ]
    search_fields = ["id"]
    list_filter = ["launch_at", "bursting_at", "landing_at", "created_at"]
