"""Django application configuration for the local jet stub."""

from __future__ import annotations

from django.apps import AppConfig


class JetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jet"
    verbose_name = "Jet Admin"
