"""Integration tests covering the QR based account flow."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from catalog.models import ApparelItem, Collection
from .models import OneTimeRegistrationToken

User = get_user_model()


class RegistrationFlowTests(APITestCase):
    """Verify that QR tokens create users and attach purchases."""

    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="staff", password="testpass123", is_staff=True
        )
        self.collection = Collection.objects.create(
            name="Test Collection", slug="test-collection"
        )
        self.item = ApparelItem.objects.create(
            name="Limited Tee",
            slug="limited-tee",
            collection=self.collection,
            rarity=ApparelItem.Rarity.RARE,
            edition_size=50,
            size=ApparelItem.Size.M,
            product_url="https://example.com/products/limited-tee",
            modifications=[],
            quantity_remaining=10,
            owner=None,
        )

    def test_registration_claim_assigns_item(self):
        self.client.force_authenticate(self.staff_user)
        create_url = reverse("accounts:registration-token-create")
        response = self.client.post(
            create_url,
            {
                "email": "customer@example.com",
                "apparel_item_ids": [self.item.id],
                "order_reference": "ORDER-1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token_value = response.data["token"]
        claim_url = reverse("accounts:registration-claim")
        claim_response = self.client.post(
            claim_url,
            {
                "token": token_value,
                "username": "customer",
                "password": "Complexpass123",
            },
            format="json",
        )
        self.assertEqual(claim_response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="customer")
        self.item.refresh_from_db()
        self.assertEqual(self.item.owner, user)
        token = OneTimeRegistrationToken.objects.get(token=token_value)
        self.assertFalse(token.is_active)


class AccountRecoveryTests(APITestCase):
    """Ensure recovery tokens reset passwords."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="recover", password="Initial123", email="recover@example.com"
        )

    def test_recovery_flow_resets_password(self):
        request_url = reverse("accounts:recovery-request")
        response = self.client.post(
            request_url,
            {"identifier": "recover"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token_value = response.data["token"]
        confirm_url = reverse("accounts:recovery-confirm")
        confirm_response = self.client.post(
            confirm_url,
            {
                "token": token_value,
                "new_password": "Newpass12345",
            },
            format="json",
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Newpass12345"))
