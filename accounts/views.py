"""REST endpoints for user profiles and simplified registration."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from .serializers import SimpleRegistrationSerializer, UserProfileSerializer

User = get_user_model()


class UserProfileView(generics.RetrieveAPIView):
    """Expose a public profile by the user's personal slug."""

    serializer_class = UserProfileSerializer
    lookup_field = "profile_slug"
    queryset = User.objects.prefetch_related(
        "apparel_units__item",
        "apparel_units__item__collection",
    )


class SimpleRegistrationView(generics.CreateAPIView):
    """Create a user by phone number and nickname."""

    serializer_class = SimpleRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
