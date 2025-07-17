import os
from django.conf import settings
import pytest

from archives.models import Archive, FileItem
from archives.tasks import build_zip

@pytest.mark.django_db
def test_build_zip_idempotent(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)

    arch = Archive.objects.create(short_code="XX", ready=False)
    fpath = tmp_path / "file.txt"
    fpath.write_text("x")
    FileItem.objects.create(archive=arch, file=str(fpath.relative_to(tmp_path)))

    build_zip.run(build_zip, arch.pk)
    arch.refresh_from_db()
    assert arch.ready

    zip_path = tmp_path / arch.zip_file.name
    mtime1 = os.path.getmtime(str(zip_path))

    build_zip.run(build_zip, arch.pk)
    mtime2 = os.path.getmtime(str(zip_path))

    assert mtime1 == mtime2