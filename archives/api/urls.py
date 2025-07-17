# archives/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArchiveViewSet, ArchiveStatsAPIView

router = DefaultRouter()
router.register(r"archives", ArchiveViewSet, basename="archive")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "archives/<str:short_code>/stats/",
        ArchiveStatsAPIView.as_view(),
        name="archive-stats",
    ),
]
