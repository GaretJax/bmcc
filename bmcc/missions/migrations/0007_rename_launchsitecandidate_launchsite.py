from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("missions", "0006_mission_mission_window"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="LaunchSiteCandidate",
            new_name="LaunchSite",
        ),
    ]
