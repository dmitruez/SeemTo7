"""URL configuration for seemtoseven project."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

from . import admin as project_admin  # noqa: F401  # ensure admin customisations are loaded

urlpatterns = [
    path("jet/", include("jet.urls", "jet")),
    path("jet/dashboard/", include("jet.dashboard.urls", "jet-dashboard")),
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/", include("catalog.urls")),
]
