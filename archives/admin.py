from django.contrib import admin
from .models import Archive, FileItem

@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display  = ("short_code", "download_count", "max_downloads", "created_at", "expires_at")
    search_fields = ("short_code",)

@admin.register(FileItem)
class FileItemAdmin(admin.ModelAdmin):
    list_display  = ("file", "archive", "uploaded_at")
    list_filter   = ("archive",)
