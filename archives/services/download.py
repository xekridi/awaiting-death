import os

from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from ..models.archive import Archive
from ..models.click_log import ClickLog


class DownloadError(Exception):
    pass

def get_archive_for_download(code, session, password=None):
    try:
        archive = Archive.objects.get(short_code=code, deleted_at__isnull=True)
    except Archive.DoesNotExist:
        raise DownloadError("Архив не найден")

    if not archive.ready:
        raise DownloadError("Архив ещё не готов")

    if archive.password:
        has_access = session.get(f"access_{archive.id}") or (
            password is not None and archive.check_password(password)
        )
        if not has_access:
            raise PermissionDenied("Неверный пароль")

    if archive.expires_at and archive.expires_at < timezone.now():
        raise DownloadError("Срок действия архива истёк")

    if archive.max_downloads and archive.download_count >= archive.max_downloads:
        raise DownloadError("Превышен лимит скачиваний")

    return archive

def mark_download_and_get_path(archive, request):
    zip_path = archive.zip_file.path if archive.zip_file else ""
    if not zip_path or not os.path.exists(zip_path):
        raise SuspiciousOperation("ZIP-файл не найден")

    with transaction.atomic():
        ClickLog.objects.create(
            archive=archive,
            ip_address=request.META.get("REMOTE_ADDR", ""),
            referer=request.META.get("HTTP_REFERER", ""),
        )
        Archive.objects.filter(pk=archive.pk).update(download_count=F("download_count") + 1)

    return zip_path
