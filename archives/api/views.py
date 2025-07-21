import os
from django.conf import settings
from django.urls import reverse

from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ArchiveSerializer
from ..models import Archive, FileItem
from ..utils import generate_qr_image
from ..business.stats import get_downloads_by_day, get_top_referers

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class ArchiveViewSet(viewsets.ModelViewSet):
    serializer_class = ArchiveSerializer

    def get_permissions(self):
        if self.action in ['create', 'upload']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsOwner()]

    def get_queryset(self):
        if self.action == "upload":
            return Archive.objects.all()
        return self.request.user.archives.filter(deleted_at__isnull=True)

    @action(detail=True, methods=['post'], url_path='upload', parser_classes=[MultiPartParser])
    def upload(self, request, pk=None):
        archive = self.get_object()
        f = request.FILES.get('file')
        if not f:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        FileItem.objects.create(archive=archive, file=f)
        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        archive = self.get_object()
        zip_name = archive.zip_file.name
        if zip_name:
            path = os.path.join(settings.MEDIA_ROOT, zip_name)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        FileItem.objects.filter(archive=archive).delete()
        archive.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def perform_create(self, serializer):
        archive = serializer.save()
        request = self.request
        preview_url = request.build_absolute_uri(
            reverse("download-page", args=[archive.short_code])
        )
        qr_file = generate_qr_image(preview_url)
        archive.qr_image.save(f"{archive.short_code}.png", qr_file, save=True)

class StatsAPIView(APIView):
    def get(self, request, short_code):
        return Response({
            "by_day": get_downloads_by_day(short_code),
            "top_referers": get_top_referers(short_code),
        })
    

class ArchiveCreateAPIView(generics.CreateAPIView):
    queryset = Archive.objects.all()
    serializer_class = ArchiveSerializer

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        return Response(resp.data, status=status.HTTP_201_CREATED)
    