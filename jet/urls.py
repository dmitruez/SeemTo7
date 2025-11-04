"""Minimal URLConf emulating django-jet dashboards."""

from __future__ import annotations

from django.http import HttpResponse
from django.urls import path


def placeholder_view(request):
    return HttpResponse("Jet admin dashboard placeholder", content_type="text/plain")


app_name = "jet"

urlpatterns = [
    path("", placeholder_view, name="dashboard"),
]
