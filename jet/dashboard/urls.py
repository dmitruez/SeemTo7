"""Minimal dashboard URL configuration."""

from __future__ import annotations

from django.http import HttpResponse
from django.urls import path


def placeholder_view(request):
    return HttpResponse("Jet dashboard placeholder", content_type="text/plain")


app_name = "jet-dashboard"

urlpatterns = [
    path("", placeholder_view, name="index"),
]
