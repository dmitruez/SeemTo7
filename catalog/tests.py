"""API tests for the catalog application."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ApparelItem, ApparelItemSizeInventory, Collection, CollectionSizeTemplate


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
        CollectionSizeTemplate.objects.create(
            collection=collection,
            size=ApparelItem.Size.M,
            quantity=80,
        )
        CollectionSizeTemplate.objects.create(
            collection=collection,
            size=ApparelItem.Size.L,
            quantity=20,
        )
        url = reverse("apparelitem-list")
        payload = {
            "name": "Hoodie",
            "slug": "hoodie",
            "collection": collection.pk,
            "rarity": "rare",
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ApparelItem.objects.count(), 1)
        item = ApparelItem.objects.get()
        self.assertEqual(item.collection, collection)
        self.assertEqual(item.total_units, 100)
        self.assertEqual(item.remaining_units, 100)
        self.assertEqual(item.units.count(), 100)
        access_codes = set(item.units.values_list("access_code", flat=True))
        self.assertEqual(len(access_codes), 100)
        inventories = ApparelItemSizeInventory.objects.filter(item=item)
        self.assertEqual(inventories.count(), 2)
        summary = {
            inv.size: inv.quantity_remaining
            for inv in inventories
        }
        self.assertEqual(
            summary,
            {
                ApparelItem.Size.L: 20,
                ApparelItem.Size.M: 80,
            },
        )

    def test_lookup_by_access_code(self) -> None:
        collection = Collection.objects.create(name="Drop", slug="drop")
        CollectionSizeTemplate.objects.create(
            collection=collection, size=ApparelItem.Size.S, quantity=10
        )
        item = ApparelItem.objects.create(
            name="Jacket",
            slug="jacket",
            collection=collection,
            rarity=ApparelItem.Rarity.EPIC,
        )
        unit = item.units.first()
        self.assertIsNotNone(unit)
        url = reverse("apparelitem-lookup", kwargs={"access_code": unit.access_code})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], unit.pk)
        self.assertEqual(response.data["access_code"], unit.access_code)
        self.assertEqual(response.data["item"], item.pk)
