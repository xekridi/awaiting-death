from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archive = serializer.save()
        build_zip.delay(str(archive.id))
        return Response(
            ArchiveSerializer(archive).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def upload(self, request, pk=None):
        archive = self.get_object()
        file_obj = request.data.get("file")
        if not file_obj:
            return Response({"detail": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        item = FileItem.objects.create(archive=archive, file=file_obj)
        return Response(FileItemSerializer(item).data, status=status.HTTP_201_CREATED)
