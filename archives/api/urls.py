from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ArchiveViewSet, StatsAPIView


router = DefaultRouter()
router.register("archive", ArchiveViewSet, basename="archive")

urlpatterns = router.urls
urlpatterns += [
    path('archive/<str:short_code>/stats/', StatsAPIView.as_view(), name='archive-stats'),
]