from django.db import migrations

import bmcc.fields


class Migration(migrations.Migration):
    dependencies = [
        ("missions", "0008_fix_negative_longitudes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="launchsite",
            name="location",
            field=bmcc.fields.CoordinateField(),
        ),
    ]
