"""App configuration for the dashboard stub."""

from __future__ import annotations

from django.apps import AppConfig


class JetDashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jet.dashboard"
    verbose_name = "Jet Dashboard"
