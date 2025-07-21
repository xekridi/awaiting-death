from rest_framework import viewsets, permissions

from .serializers import ArchiveSerializer, FileItemSerializer, ClickLogSerializer
from archives.models.archive import Archive
from archives.models.file_item import FileItem
from archives.models.click_log import ClickLog

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
