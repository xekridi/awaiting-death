
import pytest
from django.utils import timezone

from archives.models import Archive, FileItem
from archives.tasks import cleanup_expired_archives


@pytest.mark.django_db
def test_cleanup_task(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    (tmp_path / "zips").mkdir()
    zf = tmp_path / "zips" / "old.zip"
    zf.write_bytes(b"PK\x05\x06")
    arch = Archive.objects.create(
        name="name",
        short_code="OLD",
        expires_at=timezone.now() - timezone.timedelta(days=1),
        ready=True,
        zip_file="zips/old.zip"
    )
    FileItem.objects.create(archive=arch, file="uploads/old.txt")
    cleanup_expired_archives()
    assert not Archive.objects.filter(pk=arch.pk).exists()
    assert not zf.exists()
