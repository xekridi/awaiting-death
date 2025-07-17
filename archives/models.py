from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
import uuid

def default_expiry():
    return timezone.now() + timezone.timedelta(days=7)

class Archive(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_code     = models.CharField(max_length=10, unique=True)
    password       = models.CharField(max_length=128, blank=True)
    max_downloads  = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    description    = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    ready     = models.BooleanField(default=False)
    zip_file  = models.FileField(upload_to="zips/", blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    error = models.TextField(null=True, blank=True)
    build_task_id = models.CharField(max_length=50, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="archives"
    )

    def get_download_url(self) -> str:
        return reverse("download", args=[self.short_code])

    def __str__(self):
        return f"{self.short_code} ({self.download_count}/{self.max_downloads or '∞'})"


class FileItem(models.Model):
    archive     = models.ForeignKey(Archive, related_name="files", on_delete=models.CASCADE)
    file        = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ClickLog(models.Model):
    archive    = models.ForeignKey(Archive, on_delete=models.CASCADE, related_name="clicks")
    timestamp  = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()
    referer    = models.URLField(blank=True)
