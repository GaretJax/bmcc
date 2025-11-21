import os
import random
import string
from datetime import datetime

from django.utils.deconstruct import deconstructible

from django_storage_url import dsn_configured_storage_class
from slugify import slugify


DefaultStorage = dsn_configured_storage_class("PUBLIC_STORAGE_DSN")


class TextGenerator:
    def __init__(self, func):
        self.func = func

    def __str__(self):
        return self.func()


class InstanceAttrSlugifier:
    def __init__(self, value):
        self.value = value

    def __getattr__(self, name):
        return InstanceAttrSlugifier(getattr(self.value, name))

    def __str__(self):
        return slugify(
            str(self.value).strip(), lower=False, only_ascii=True
        ).strip("-")


def randomword(length):
    return "".join(
        random.choice(string.ascii_lowercase + string.digits)
        for i in range(length)
    )


class RandomFactory:
    def __getitem__(self, key):
        return TextGenerator(lambda: randomword(int(key)))


@deconstructible
class UploadPattern:
    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, instance, filename):
        filename, ext = os.path.splitext(filename)
        now = datetime.utcnow().replace(microsecond=0)
        return self.pattern.format(
            raw_filename=filename,
            filename=slugify(filename),
            ext=ext.strip(".").lower(),
            rand=RandomFactory(),
            datetime=now.isoformat(),
            date=now.date().isoformat(),
            o=InstanceAttrSlugifier(instance),
        )
