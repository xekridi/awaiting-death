from django.urls import reverse
from rest_framework import serializers

from archives.models.archive import Archive
from archives.models.click_log import ClickLog
from archives.models.file_item import FileItem
from archives.utils import generate_qr_image


class ArchiveSerializer(serializers.ModelSerializer):
    short_code = serializers.CharField(read_only=True)
    name = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    qr_image = serializers.ImageField(read_only=True)

    class Meta:
        model = Archive
        fields = ["short_code", "name", "max_downloads", "expires_at", "password", "qr_image"]

    def create(self, validated_data):
        validated_data["name"] = validated_data.get("name") or validated_data.get("short_code")
        pwd = validated_data.pop("password", "")
        archive = Archive.objects.create(**validated_data)
        archive.password = pwd
        archive.save(update_fields=["password"])

        preview_url = self.context["request"].build_absolute_uri(
            reverse("download-page", args=[archive.short_code])
        )
        archive.qr_image.save(f"{archive.short_code}.png", generate_qr_image(preview_url), save=True)
        return archive

class FileItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = FileItem
        fields = ["id", "archive", "file", "created_at"]
        read_only_fields = ["id", "created_at"]

class ClickLogSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ClickLog
        fields = ["id", "archive", "timestamp", "ip_address", "referer"]
        read_only_fields = ["id", "timestamp"]
