from django.db import models

from .archive import Archive


class FileItem(models.Model):
    archive     = models.ForeignKey(Archive, related_name="files", on_delete=models.CASCADE)
    file        = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
