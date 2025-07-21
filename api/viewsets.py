from rest_framework import permissions, viewsets

from archives.models.archive import Archive
from archives.models.click_log import ClickLog
from archives.models.file_item import FileItem

from .serializers import ArchiveSerializer, ClickLogSerializer, FileItemSerializer


class ArchiveViewSet(viewsets.ModelViewSet):
    queryset = Archive.objects.all()
    serializer_class = ArchiveSerializer
    permission_classes = [permissions.IsAuthenticated]

class FileItemViewSet(viewsets.ModelViewSet):
    queryset = FileItem.objects.all()
    serializer_class = FileItemSerializer
    permission_classes = [permissions.IsAuthenticated]

class ClickLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClickLog.objects.all()
    serializer_class = ClickLogSerializer
    permission_classes = [permissions.IsAuthenticated]
