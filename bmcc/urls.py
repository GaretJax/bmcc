from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _


admin.site.site_header = settings.ADMIN_SITE_HEADER


urlpatterns = i18n_patterns(
    path(_("admin/"), admin.site.urls),
    path("tracking/", include("bmcc.tracking.urls")),
    prefix_default_language=False,
)

if settings.ENVIRONMENT == "local":
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
