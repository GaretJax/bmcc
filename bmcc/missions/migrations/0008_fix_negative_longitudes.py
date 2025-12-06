from django.db import migrations

from bmcc.fields import Coordinate


def fix_longitudes(apps, schema_editor):
    LaunchSite = apps.get_model("missions", "LaunchSite")
    for site in LaunchSite.objects.all():
        if site.location.x < 0:
            site.location = Coordinate(
                360 - abs(site.location.x), site.location.y
            )
            site.save(update_fields=["location"])


class Migration(migrations.Migration):
    dependencies = [
        ("missions", "0007_rename_launchsitecandidate_launchsite"),
    ]

    operations = [
        migrations.RunPython(fix_longitudes, migrations.RunPython.noop),
    ]
