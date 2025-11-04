"""API tests for the catalog application."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ApparelItem, Collection


class CatalogAPITests(APITestCase):
    """Ensure the catalog endpoints provide the expected behaviour."""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="secret",
            phone_number="+75555555555",
        )

    def test_create_collection(self) -> None:
        url = reverse("collection-list")
        payload = {
            "name": "Limited Drop",
            "slug": "limited-drop",
            "description": "Exclusive capsule collection",
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects.count(), 1)
        collection = Collection.objects.get()
        self.assertEqual(collection.name, payload["name"])

    def test_create_apparel_item(self) -> None:
        collection = Collection.objects.create(
            name="Limited Drop",
            slug="limited-drop",
        )
        url = reverse("apparelitem-list")
        payload = {
            "name": "Hoodie",
            "slug": "hoodie",
            "collection": collection.pk,
            "rarity": "rare",
            "edition_size": 100,
            "size": "M",
            "product_url": "https://example.com/hoodie",
            "modifications": ["Glow in the dark"],
            "owner_id": self.user.pk,
            "quantity_remaining": 80,
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ApparelItem.objects.count(), 1)
        item = ApparelItem.objects.get()
        self.assertEqual(item.owner, self.user)
        self.assertEqual(item.collection, collection)
        self.assertTrue(item.qr_code_url.startswith("https://api.qrserver.com"))
