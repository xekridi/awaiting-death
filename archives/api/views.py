from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from archives.models import Archive, FileItem
from archives.tasks import build_zip
from .serializers import ArchiveSerializer, FileItemSerializer
from archives.business.stats import get_downloads_by_day, get_top_referers


class ArchiveStatsAPIView(APIView):
    def get(self, request, short_code):
        by_day = get_downloads_by_day(short_code)
        referers = get_top_referers(short_code)
        return Response({"by_day": by_day, "top_referers": referers})

class ArchiveViewSet(viewsets.ModelViewSet):
    queryset = Archive.objects.all()
    serializer_class = ArchiveSerializer

    @action(detail=True, methods=["post"], url_path="upload")
    def upload(self, request, pk=None):
        serializer = FileItemSerializer(
            data={"file": request.FILES["file"], "archive": pk}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        archive = self.get_object()
        return Response({
            "by_day":       get_downloads_by_day(archive.short_code),
            "top_referers": get_top_referers(archive.short_code),
        })

class StatsByCodeAPIView(APIView):
    def get(self, request, short_code):
        arch = Archive.objects.filter(short_code=short_code).first()
        if not arch:
            return Response({"detail": "Not found."}, status=404)
        return Response({
            "by_day":       get_downloads_by_day(short_code),
            "top_referers": get_top_referers(short_code),
        })