from django.db import migrations

import bmcc.fields


class Migration(migrations.Migration):
    dependencies = [
        ("predictions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prediction",
            name="launch_location",
            field=bmcc.fields.CoordinateField(),
        ),
        migrations.AlterField(
            model_name="prediction",
            name="burst_location",
            field=bmcc.fields.CoordinateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="prediction",
            name="landing_location",
            field=bmcc.fields.CoordinateField(blank=True, null=True),
        ),
    ]
