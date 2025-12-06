from django.db import migrations

import bmcc.fields


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0010_merge_0002_asset_launch_site_0009_ping_prediction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ping",
            name="position",
            field=bmcc.fields.CoordinateField(),
        ),
    ]
