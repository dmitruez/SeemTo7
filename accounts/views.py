"""REST endpoints implementing QR based registration and recovery flows."""

from __future__ import annotations

import base64
import io
from typing import Any

import qrcode
from django.contrib.auth import get_user_model
from django.db import transaction
from django.urls import reverse
from rest_framework import generics, permissions, response, status
from rest_framework.views import APIView

from .models import OneTimeRegistrationToken
from .serializers import (
    AccountRecoveryConfirmSerializer,
    AccountRecoveryRequestSerializer,
    RegistrationClaimSerializer,
    RegistrationQRCodeSerializer,
    RegistrationTokenCreateSerializer,
    UserProfileSerializer,
)

User = get_user_model()


def build_qr_payload(request, token: OneTimeRegistrationToken) -> str:
    """Generate a base64 encoded QR image that points to the registration endpoint."""

    claim_url = request.build_absolute_uri(
        reverse("accounts:registration-claim") + f"?token={token.token}"
    )
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(claim_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class UserProfileView(generics.RetrieveAPIView):
    """Expose a public profile by the user's personal slug."""

    serializer_class = UserProfileSerializer
    lookup_field = "profile_slug"
    queryset = User.objects.prefetch_related(
        "apparel_items__collection",
    )


class RegistrationTokenCreateView(APIView):
    """Create a one-time registration token and return its QR representation."""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args: Any, **kwargs: Any):
        serializer = RegistrationTokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.create_token()
        qr_image = build_qr_payload(request, token)
        return response.Response(
            {
                "token": str(token.token),
                "qr_image": qr_image,
                "expires_at": token.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )


class RegistrationClaimView(APIView):
    """Exchange a QR token for a full account."""

    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, *args: Any, **kwargs: Any):
        serializer = RegistrationClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create_user()
        return response.Response(
            {
                "id": user.id,
                "username": user.username,
                "profile_slug": user.profile_slug,
                "profile_url": request.build_absolute_uri(user.profile_url),
            },
            status=status.HTTP_201_CREATED,
        )


class RegistrationQRCodeView(APIView):
    """Return the QR representation for an existing token."""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args: Any, **kwargs: Any):
        serializer = RegistrationQRCodeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        token = OneTimeRegistrationToken.objects.get(token=serializer.validated_data["token"])
        qr_image = build_qr_payload(request, token)
        return response.Response({"qr_image": qr_image})


class AccountRecoveryRequestView(APIView):
    """Initiate the recovery flow by issuing a token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args: Any, **kwargs: Any):
        serializer = AccountRecoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()
        if not user:
            return response.Response(
                {"detail": "Если аккаунт существует, ссылка отправлена."},
                status=status.HTTP_200_OK,
            )
        token = serializer.create_token(user)
        # In production this would be emailed or sent via SMS.
        return response.Response(
            {
                "detail": "Ссылка восстановления сгенерирована.",
                "token": str(token.token),
                "expires_at": token.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )


class AccountRecoveryConfirmView(APIView):
    """Reset the password using a recovery token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args: Any, **kwargs: Any):
        serializer = AccountRecoveryConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.update_password()
        return response.Response(
            {
                "detail": "Пароль успешно обновлен.",
                "username": user.username,
            },
            status=status.HTTP_200_OK,
        )
