"""Routing for account related API endpoints."""

from django.urls import path

from .views import SimpleRegistrationView, UserProfileView

app_name = "accounts"

urlpatterns = [
    path("profiles/<slug:profile_slug>/", UserProfileView.as_view(), name="profile-detail"),
    path("registration/", SimpleRegistrationView.as_view(), name="registration"),
]
