import pytest
from django.db import IntegrityError
from django.utils import timezone

from archives.models.archive import Archive
from archives.models.click_log import ClickLog
from archives.models.file_item import FileItem


@pytest.mark.django_db
def test_archive_name_is_required():
    with pytest.raises(IntegrityError):
        Archive.objects.create(short_code="NOCODE")

@pytest.mark.django_db
def test_archive_str_returns_short_code():
    arch = Archive.objects.create(
        name="sample",
        short_code="ABC123",
        max_downloads=5,
        expires_at=timezone.now() + timezone.timedelta(days=1),
    )
    assert str(arch).startswith("ABC123")

@pytest.mark.django_db
def test_archive_default_fields(user):
    arch = Archive.objects.create(
        name="test",
        short_code="DEF456",
        owner=user,
    )
    assert arch.download_count == 0
    assert not arch.ready

@pytest.mark.django_db
def test_fileitem_association_with_archive(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    arch = Archive.objects.create(name="test", short_code="XYZ789")
    file_item = FileItem.objects.create(
        archive=arch,
        file="uploads/test.txt",
    )
    assert file_item.archive == arch
    assert arch.fileitem_set.count() == 1

@pytest.mark.django_db
def test_get_download_url_returns_correct_path():
    arch = Archive.objects.create(name="test", short_code="URL1")
    url = arch.get_download_url()
    assert url.endswith(f"/d/{arch.short_code}/file/")

@pytest.mark.django_db
def test_click_log_fields(user):
    arch = Archive.objects.create(
        name="test",
        short_code="CL1",
        owner=user,
    )
    click = ClickLog.objects.create(
        archive=arch,
        ip_address="127.0.0.1",
        referer="http://example.com",
    )
    assert click.archive == arch
    assert click.ip_address == "127.0.0.1"
    assert click.referer == "http://example.com"
