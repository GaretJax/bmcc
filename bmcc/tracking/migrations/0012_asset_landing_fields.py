from django.db import migrations, models

import bmcc.fields


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0011_alter_ping_position"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="landed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="asset",
            name="landing_location",
            field=bmcc.fields.CoordinateField(blank=True, null=True),
        ),
    ]
