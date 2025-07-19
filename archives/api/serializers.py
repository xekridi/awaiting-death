from rest_framework import serializers
from archives.models import Archive, FileItem

class ArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Archive
        fields = "__all__"

class FileItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FileItem
        fields = ("id", "file", "archive")
