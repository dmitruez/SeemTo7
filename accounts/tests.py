"""Integration tests covering the simplified account flow."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import ApparelItem, Collection

User = get_user_model()


class AccountRegistrationTests(APITestCase):
    """Verify that users can register with phone number and nickname."""

    def test_registration_creates_user_with_qr(self):
        url = reverse("accounts:registration")
        payload = {"nickname": "customer", "phone_number": "+79999999999"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="customer").exists())
        user = User.objects.get(username="customer")
        self.assertEqual(user.phone_number, "+79999999999")
        self.assertTrue(user.qr_code_url)
        self.assertEqual(response.data["nickname"], "customer")
        self.assertTrue(response.data["qr_code_url"].startswith("https://api.qrserver.com"))

    def test_profile_returns_qr_and_items(self):
        user = User.objects.create(username="collector", phone_number="+78888888888")
        user.set_unusable_password()
        user.save()
        collection = Collection.objects.create(name="Drop", slug="drop")
        item = ApparelItem.objects.create(
            name="Limited Tee",
            slug="limited-tee",
            collection=collection,
            rarity=ApparelItem.Rarity.RARE,
            edition_size=50,
            size=ApparelItem.Size.M,
            product_url="https://example.com/products/limited-tee",
            modifications=[],
            quantity_remaining=10,
            owner=user,
        )
        url = reverse("accounts:profile-detail", kwargs={"profile_slug": user.profile_slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], "collector")
        self.assertTrue(response.data["qr_code_url"].startswith("https://api.qrserver.com"))
        self.assertEqual(len(response.data["purchased_items"]), 1)
        self.assertEqual(response.data["purchased_items"][0]["id"], item.id)
        self.assertTrue(
            response.data["purchased_items"][0]["qr_code_url"].startswith("https://api.qrserver.com")
        )
