from rest_framework.routers import DefaultRouter
from .viewsets import ArchiveViewSet, FileItemViewSet, ClickLogViewSet

router = DefaultRouter()
router.register(r"archives", ArchiveViewSet, basename="archive")
router.register(r"files", FileItemViewSet, basename="fileitem")
router.register(r"clicks", ClickLogViewSet, basename="clicklog")
    