import django.contrib.postgres.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("missions", "0005_launchsitecandidate_prediction_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="mission",
            name="mission_window",
            field=django.contrib.postgres.fields.DateTimeRangeField(
                blank=True, null=True
            ),
        ),
    ]
