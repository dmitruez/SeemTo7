"""Routing for account related API endpoints."""

from django.urls import path

from .views import (
    AccountRecoveryConfirmView,
    AccountRecoveryRequestView,
    RegistrationClaimView,
    RegistrationQRCodeView,
    RegistrationTokenCreateView,
    UserProfileView,
)

app_name = "accounts"

urlpatterns = [
    path("profiles/<slug:profile_slug>/", UserProfileView.as_view(), name="profile-detail"),
    path("registration/token/", RegistrationTokenCreateView.as_view(), name="registration-token-create"),
    path("registration/claim/", RegistrationClaimView.as_view(), name="registration-claim"),
    path("registration/qr/", RegistrationQRCodeView.as_view(), name="registration-qr"),
    path("recovery/request/", AccountRecoveryRequestView.as_view(), name="recovery-request"),
    path("recovery/confirm/", AccountRecoveryConfirmView.as_view(), name="recovery-confirm"),
]
