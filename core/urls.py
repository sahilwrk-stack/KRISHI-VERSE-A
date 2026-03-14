from django.urls import path
from core import views

app_name = "core"

urlpatterns = [
    # Main pages
    path("",             views.index,              name="index"),
    path("analysis/",    views.analysis_dashboard, name="analysis"),
    path("dashboard/",   views.analysis_dashboard, name="dashboard"),  # legacy alias
    path("analyze/",     views.analyze,            name="analyze"),    # legacy alias
    path("compare/",     views.compare,            name="compare"),    # legacy alias
]
# Note: AJAX/API endpoints are registered at project level (agriverse/urls.py)
# so they work without a language prefix in JavaScript fetch() calls.
