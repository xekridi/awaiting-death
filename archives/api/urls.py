from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArchiveViewSet, StatsAPIView

urlpatterns = [
    path("archive/<str:short_code>/stats/", StatsAPIView.as_view(), name="archive-stats"),
]

router = DefaultRouter()
router.register("archive", ArchiveViewSet, basename="archive")

urlpatterns += [
     path("", include(router.urls)),
]