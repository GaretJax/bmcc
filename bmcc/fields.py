import uuid

from django import forms
from django.contrib.gis.db import models as geo_models
from django.contrib.gis.db.models.fields import SpatialProxy
from django.contrib.gis.geos import GEOSGeometry, Point
from django.db import models
from django.db.models import UUIDField
from django.db.models.base import NOT_PROVIDED
from django.utils.functional import keep_lazy
from django.utils.html import format_html
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


class UUIDAutoField(UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("primary_key", True)
        kwargs.setdefault("default", uuid.uuid4)
        kwargs.setdefault("editable", False)
        super().__init__(*args, **kwargs)

    def _check_max_length_warning(self):
        return []

    def get_prep_value(self, value):
        return self.to_python(value)


class ConfiguredInstanceProxy:
    def __init__(self, field, classpath_field_name, config_field_name):
        self.field = field
        self.cache_field_name = f"_{self.field.name}_cache"
        self.classpath_field_name = classpath_field_name
        self.config_field_name = config_field_name

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        if not hasattr(obj, self.cache_field_name):
            instance_class_path = getattr(obj, self.classpath_field_name)
            if instance_class_path:
                if self.field.is_configurable:
                    instance_config = getattr(obj, self.config_field_name)
                else:
                    instance_config = {}
                if self.field.takes_instance:
                    args = [obj]
                else:
                    args = []
                instance_class = import_string(instance_class_path)
                constructor = (
                    getattr(instance_class, self.field.constructor)
                    if self.field.constructor
                    else instance_class
                )
                instance = constructor(*args, **instance_config)
            else:
                instance = None
            setattr(obj, self.cache_field_name, instance)
        return getattr(obj, self.cache_field_name)

    def __set__(self, obj, value):
        raise RuntimeError(
            f"`{obj.__class__.__name__}.{self.field.name} cannot` be set "
            f"directly; please set the `{self.classpath_field_name}` and "
            f"`{self.config_field_name}` fields instead"
        )

    def __delete__(self, obj):
        if hasattr(obj, self.cache_field_name):
            delattr(obj, self.cache_field_name)

    def instantiation_log(self, obj):
        try:
            backend = getattr(obj, self.field.name)
        except Exception as e:
            return format_html(
                (
                    '<p style="color: red; font-weight: bold; margin-bottom: 0.1em">{}</p>'
                    "<code>{}</code>"
                ),
                _("Instantiation failed"),
                e,
            )
        else:
            return format_html(
                (
                    '<p style="color: green; font-weight: bold; margin-bottom: 0.1em">{}</p>'
                    "<code>{}</code>"
                ),
                _("Instantiation successful"),
                repr(backend),
            )

    instantiation_log.short_description = _("Instantiation log")


@keep_lazy(str)
def lazy_formatted_string(template, *args, **kwargs):
    return template.format(*args, **kwargs)


class ConfigurableInstanceField:
    auto_created = False
    concrete = False
    editable = False
    hidden = False
    is_relation = False

    def __init__(
        self,
        *,
        choices,
        default="",
        null=False,
        constructor=None,
        takes_instance=False,
        is_configurable=True,
        verbose_name=None,
    ):
        self.choices = choices
        self.default = default
        self.null = null
        self.constructor = constructor
        self.takes_instance = takes_instance
        self.is_configurable = is_configurable
        self.verbose_name = verbose_name

    def contribute_to_class(self, cls, name):
        self.name = name
        # TODO: save(update_fields=["field_name"]) will not work...

        default = self.default or NOT_PROVIDED

        max_length = max(len(c.value) for c in self.choices)

        if self.verbose_name is None and name:
            verbose_name = name.replace("_", " ")
        else:
            verbose_name = self.verbose_name

        classpath_field_name = f"{name}_class_path"
        classpath_field = models.CharField(
            verbose_name=lazy_formatted_string(
                _("{verbose_name} class path"),
                verbose_name=verbose_name,
            ),
            default=default,
            choices=self.choices,
            max_length=max_length,
            blank=self.null,
        )
        cls.add_to_class(classpath_field_name, classpath_field)

        if self.is_configurable:
            config_field_name = f"{name}_config"
            config_field = models.JSONField(
                verbose_name=lazy_formatted_string(
                    _("{verbose_name} configuration"),
                    verbose_name=verbose_name,
                ),
                default=dict,
                blank=True,
                null=self.null,
            )
            cls.add_to_class(config_field_name, config_field)
        else:
            config_field_name = None

        setattr(
            cls,
            name,
            ConfiguredInstanceProxy(
                self, classpath_field_name, config_field_name
            ),
        )


class Coordinate(Point):
    @property
    def latitude(self):
        return self.y

    @property
    def longitude(self):
        return self.x

    @property
    def abs_longitude(self):
        if self.longitude < 0:
            return 360 + self.longitude
        return self.longitude

    lat = latitude
    lon = longitude
    abs_lon = abs_longitude


class CoordinateWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (
            forms.NumberInput(attrs={"step": "0.00001"}),
            forms.NumberInput(attrs={"step": "0.00001"}),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.y, value.x]
        return [None, None]


class CoordinateFormField(forms.MultiValueField):
    widget = CoordinateWidget

    def __init__(self, *args, **kwargs):
        kwargs.pop("geom_type", None)
        kwargs.pop("srid", None)
        kwargs.pop("dim", None)
        kwargs.pop("geography", None)
        fields = (
            forms.FloatField(required=False),
            forms.FloatField(required=False),
        )
        super().__init__(fields, *args, require_all_fields=False, **kwargs)

    def compress(self, data_list):
        if data_list is None:
            return None
        lat, lon = data_list
        if lat in (None, "") and lon in (None, ""):
            return None
        if lat in (None, "") or lon in (None, ""):
            raise forms.ValidationError(
                "Both latitude and longitude are required."
            )
        return Coordinate(float(lon), float(lat))


class CoordinateProxy(SpatialProxy):
    def __set__(self, obj, value):
        if isinstance(value, Point) and not isinstance(value, Coordinate):
            value = Coordinate(value.x, value.y, srid=value.srid)
        super().__set__(obj, value)


class CoordinateField(geo_models.PointField):
    geom_class = Coordinate

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("geography", True)
        kwargs.setdefault("dim", 2)
        super().__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(
            cls,
            self.attname,
            CoordinateProxy(self.geom_class, self, load_func=GEOSGeometry),
        )
