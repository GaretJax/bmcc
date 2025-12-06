import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("missions", "0007_rename_launchsitecandidate_launchsite"),
        ("tracking", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="launch_site",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assets",
                to="missions.launchsite",
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="launched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
