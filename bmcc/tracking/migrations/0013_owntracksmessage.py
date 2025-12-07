from django.db import migrations, models

import bmcc.fields


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0012_asset_landing_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="OwnTracksMessage",
            fields=[
                (
                    "id",
                    bmcc.fields.UUIDAutoField(
                        primary_key=True, serialize=False
                    ),
                ),
                ("message", models.JSONField()),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "beacon",
                    models.ForeignKey(
                        on_delete=models.CASCADE,
                        related_name="owntracks_messages",
                        to="tracking.beacon",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
