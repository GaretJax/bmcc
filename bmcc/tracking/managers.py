from django.db import models


class BeaconQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)
