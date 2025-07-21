from .archive import Archive

from django.db import models
from django.utils import timezone

class ClickLog(models.Model):
    archive     = models.ForeignKey(Archive, on_delete=models.CASCADE, related_name="clicks")
    timestamp   = models.DateTimeField(default=timezone.now)
    ip_address  = models.GenericIPAddressField()
    referer     = models.URLField(blank=True)
