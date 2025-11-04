"""URL routes for the catalog API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApparelItemViewSet, CollectionViewSet

router = DefaultRouter()
router.register(r"collections", CollectionViewSet)
router.register(r"apparel", ApparelItemViewSet)

urlpatterns = [path("", include(router.urls))]
