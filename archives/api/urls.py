from rest_framework.routers import DefaultRouter
from django.urls import path, include
from accounts.views import SignUpView, CustomLogoutView
from .views import ArchiveViewSet, StatsByCodeAPIView


router = DefaultRouter()
router.register("archive", ArchiveViewSet, basename="archive")

urlpatterns = router.urls
urlpatterns += [
    path("stats/<str:short_code>/", StatsByCodeAPIView.as_view(), name="archive-stats"),
]