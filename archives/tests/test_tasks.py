import os
import pytest
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from archives.models import Archive, FileItem
from archives.tasks import build_zip


@pytest.mark.django_db
def test_build_zip_idempotent(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

    arch = Archive.objects.create(
        short_code="XX",
        ready=False,
        expires_at=timezone.now() + timezone.timedelta(days=1),
    )
    file_obj = SimpleUploadedFile("file.txt", b"x")
    FileItem.objects.create(archive=arch, file=file_obj)

    res1 = build_zip.apply(args=[arch.pk]).get()
    arch.refresh_from_db()
    assert arch.ready is True
    assert res1.endswith(".zip")

    zip_path = Path(tmp_path) / res1
    assert zip_path.exists()
    mtime1 = zip_path.stat().st_mtime

    res2 = build_zip.apply(args=[arch.pk]).get()
    mtime2 = zip_path.stat().st_mtime

    assert res1 == res2
    assert mtime1 == mtime2

def test_build_zip_saves_in_zips(tmp_path, settings, archive, file_item):
    settings.MEDIA_ROOT = str(tmp_path)
    archive.ready = False
    archive.save(update_fields=["ready"])
    res = build_zip.run(archive.id)
    assert res.startswith("zips/")
    filepath = tmp_path / res
    assert filepath.exists()