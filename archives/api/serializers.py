from rest_framework import serializers
from archives.models import Archive, FileItem

class FileItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileItem
        fields = ("id", "file", "uploaded_at")

class ArchiveSerializer(serializers.ModelSerializer):
    files = FileItemSerializer(many=True, read_only=True)
    class Meta:
        model = Archive
        fields = (
            "id",
            "short_code",
            "password",
            "max_downloads",
            "download_count",
            "description",
            "created_at",
            "expires_at",
            "files",
        )
        read_only_fields = ("download_count", "created_at")
