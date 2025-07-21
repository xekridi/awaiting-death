import os
import pytest
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.utils import timezone

from archives.services.download import (
    get_archive_for_download,
    mark_download_and_get_path,
    DownloadError,
)
from archives.models.archive import Archive
from archives.models.click_log import ClickLog

@pytest.mark.django_db
def test_get_archive_for_download_not_ready(archive):
    with pytest.raises(DownloadError):
        get_archive_for_download(archive.short_code, {})

@pytest.mark.django_db
def test_get_archive_for_download_with_password_protection(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    arch = Archive.objects.create(
        name="test",
        short_code="PWD1",
        ready=True,
        password="secret",
    )
    with pytest.raises(PermissionDenied):
        get_archive_for_download(arch.short_code, {}, password="wrong")

@pytest.mark.django_db
def test_get_archive_for_download_expired():
    arch = Archive.objects.create(
        name="test",
        short_code="EXP1",
        ready=True,
        expires_at=timezone.now() - timezone.timedelta(days=1),
    )
    with pytest.raises(DownloadError):
        get_archive_for_download(arch.short_code, {})

@pytest.mark.django_db
def test_get_archive_for_download_limit_exceeded():
    arch = Archive.objects.create(
        name="test",
        short_code="LIM1",
        ready=True,
        max_downloads=1,
        download_count=1,
    )
    with pytest.raises(DownloadError):
        get_archive_for_download(arch.short_code, {})

@pytest.mark.django_db
def test_mark_download_and_get_path_success(tmp_path, settings, archive):
    settings.MEDIA_ROOT = str(tmp_path)
    zip_dir = tmp_path / "zips"
    zip_dir.mkdir()
    zip_file = zip_dir / "file.zip"
    zip_file.write_bytes(b"data")
    archive.zip_file.name = "zips/file.zip"
    archive.ready = True
    archive.save(update_fields=["zip_file", "ready"])
    path = mark_download_and_get_path(archive)
    assert os.path.exists(path)
    archive.refresh_from_db()
    assert archive.download_count == 1
    assert ClickLog.objects.filter(archive=archive).exists()

@pytest.mark.django_db
def test_mark_download_and_get_path_raises_if_missing(tmp_path, settings, archive):
    settings.MEDIA_ROOT = str(tmp_path)
    archive.ready = True
    archive.save(update_fields=["ready"])
    with pytest.raises(SuspiciousOperation):
        mark_download_and_get_path(archive)
