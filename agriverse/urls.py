from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from core import views as core_views

# ── Language-independent routes ────────────────────────────────────────────
#   set_language view + AJAX/API endpoints live outside i18n_patterns so that
#   JavaScript fetch('/ajax/farm/') always resolves regardless of active locale.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),      # set_language view

    # AJAX endpoints (called by JS with hardcoded paths)
    path("ajax/farm/",        core_views.ajax_farm,        name="ajax_farm"),
    path("ajax/market/",      core_views.ajax_market,      name="ajax_market"),
    # API endpoints
    path("api/soil-types/",   core_views.api_soil_types,   name="api_soil_types"),
    path("api/state-crops/",  core_views.api_state_crops,  name="api_state_crops"),
]

# ── Language-prefixed page routes ──────────────────────────────────────────
#   prefix_default_language=False → English keeps /analysis/
#                                   Hindi uses  /hi/analysis/  etc.
urlpatterns += i18n_patterns(
    path("", include("core.urls")),
    prefix_default_language=False,
)
