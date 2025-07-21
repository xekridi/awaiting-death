from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password
import uuid


def default_expiry():
    return timezone.now() + timezone.timedelta(days=7)

class Archive(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    short_code      = models.CharField(max_length=10, unique=True)
    name            = models.CharField(max_length=120)
    password        = models.CharField(max_length=128, blank=True, help_text="Hashed archive password")
    max_downloads   = models.PositiveIntegerField(default=0)
    download_count  = models.PositiveIntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)
    expires_at      = models.DateTimeField(null=True, blank=True)
    ready           = models.BooleanField(default=False)
    zip_file        = models.FileField(upload_to="zips/", blank=True, null=True)
    description     = models.CharField(max_length=255, blank=True)
    error           = models.TextField(null=True, blank=True)
    build_task_id   = models.CharField(max_length=50, null=True, blank=True)
    deleted_at      = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.UUIDField(
                        default=uuid.uuid4, editable=False, unique=True
                     )
    owner           = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        null=True,
                        blank=True,
                        related_name="archives",
                     )
    qr_image        = models.ImageField(
                        upload_to="qr_codes/",
                        blank=True,
                        null=True,
                        verbose_name="QR-код"
                    )

    def set_password(self, raw_password: str | None) -> None:
            self.password = make_password(raw_password) if raw_password else ""

    def check_password(self, raw_password: str | None) -> bool:
        if not self.password:
            return True
        return check_password(raw_password or "", self.password)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.short_code
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def get_download_url(self) -> str:
        return reverse("download", args=[self.short_code])

    def __str__(self):
        return f"{self.short_code} ({self.download_count}/{self.max_downloads or '∞'})"


class FileItem(models.Model):
    archive     = models.ForeignKey(Archive, related_name="files", on_delete=models.CASCADE)
    file        = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ClickLog(models.Model):
    archive     = models.ForeignKey(Archive, on_delete=models.CASCADE, related_name="clicks")
    timestamp   = models.DateTimeField(default=timezone.now)
    ip_address  = models.GenericIPAddressField()
    referer     = models.URLField(blank=True)
