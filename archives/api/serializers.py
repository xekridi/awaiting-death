from django.urls import reverse
from rest_framework import serializers

from ..models import Archive
from ..utils import generate_qr_image


class ArchiveSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model  = Archive
        fields = ["short_code", "name", "max_downloads", "expires_at",
                  "password", "qr_image"]
        read_only_fields = ["qr_image"]

    def create(self, validated):
        validated["name"] = validated.get("name") or validated["short_code"]
        pwd = validated.pop("password", "")
        archive = Archive.objects.create(**validated)
        archive.password = pwd
        archive.save()

        preview = self.context["request"].build_absolute_uri(
            reverse("download-page", args=[archive.short_code])
        )
        archive.qr_image.save(f"{archive.short_code}.png",
                              generate_qr_image(preview), save=True)
        return archive
