"""Application configuration for the catalog app."""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Basic application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"
