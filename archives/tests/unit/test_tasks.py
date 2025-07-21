from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from archives.models.archive import Archive
from archives.models.file_item import FileItem
from archives.tasks import build_zip, cleanup_expired_archives


@pytest.mark.django_db
def test_build_zip_creates_zip_and_marks_ready(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    arch = Archive.objects.create(
        name="tasktest",
        short_code="BT1",
        ready=False,
        expires_at=timezone.now() + timezone.timedelta(days=1),
    )
    FileItem.objects.create(
        archive=arch,
        file=SimpleUploadedFile("file.txt", b"data"),
    )
    result = build_zip.apply(args=[arch.id]).get()
    arch.refresh_from_db()
    zip_path = Path(settings.MEDIA_ROOT) / result
    assert arch.ready
    assert zip_path.exists()

@pytest.mark.django_db
def test_build_zip_is_idempotent(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    arch = Archive.objects.create(
        name="tasktest2",
        short_code="BT2",
        ready=False,
        expires_at=timezone.now() + timezone.timedelta(days=1),
    )
    FileItem.objects.create(
        archive=arch,
        file=SimpleUploadedFile("file2.txt", b"x"),
    )
    res1 = build_zip.apply(args=[arch.id]).get()
    m1 = (Path(settings.MEDIA_ROOT) / res1).stat().st_mtime
    res2 = build_zip.apply(args=[arch.id]).get()
    m2 = (Path(settings.MEDIA_ROOT) / res2).stat().st_mtime
    assert res1 == res2
    assert m1 == m2

@pytest.mark.django_db
def test_cleanup_expired_archives_removes_files_and_records(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    expired_dir = Path(settings.MEDIA_ROOT) / "expired"
    expired_dir.mkdir(parents=True)
    zip_file = expired_dir / "old.zip"
    zip_file.write_bytes(b"zipdata")
    arch = Archive.objects.create(
        name="oldarch",
        short_code="CLN1",
        ready=True,
        expires_at=timezone.now() - timezone.timedelta(hours=1),
        zip_file=str(zip_file.relative_to(settings.MEDIA_ROOT)),
    )
    cleanup_expired_archives()
    assert not Archive.objects.filter(pk=arch.pk).exists()
    assert not zip_file.exists()
