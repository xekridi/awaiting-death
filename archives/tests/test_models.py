import pytest
from django.utils import timezone
from archives.models import Archive, FileItem

@pytest.mark.django_db
def test_archive_and_fileitem_creation(tmp_path, settings):
    arch = Archive.objects.create(
        short_code="ABC123",
        max_downloads=5,
        expires_at=timezone.now() + timezone.timedelta(days=1)
    )
    assert str(arch).startswith("ABC123")

    dummy = tmp_path / "test.txt"
    dummy.write_text("hello")

    fi = FileItem.objects.create(
        archive=arch,
        file=f"uploads/{dummy.name}"
    )

    assert fi.archive == arch
    assert arch.files.count() == 1
