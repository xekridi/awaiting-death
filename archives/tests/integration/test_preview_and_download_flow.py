import pytest
from django.urls import reverse

from archives.models.archive import Archive


@pytest.fixture
def zip_archive(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    filename = "archive.zip"
    path = tmp_path / filename
    path.write_bytes(b"PK\x05\x06")
    return filename

@pytest.mark.django_db
def test_preview_wait_page_shown_for_non_ready_archive(client_logged_in):
    arch = Archive.objects.create(short_code="wait1", ready=False, max_downloads=0)
    url = reverse("download-page", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    assert "Пожалуйста, подождите" in content

@pytest.mark.django_db
def test_preview_lists_files_when_archive_ready(client_logged_in, zip_archive):
    arch = Archive.objects.create(short_code="pr1", ready=True, max_downloads=0)
    arch.zip_file.name = zip_archive
    arch.save(update_fields=["zip_file"])
    url = reverse("download-page", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    assert "<li" in content

@pytest.mark.django_db
def test_direct_download_endpoint_requires_password_if_set(client_logged_in, zip_archive):
    arch = Archive.objects.create(short_code="dl1", ready=True, password="secret")
    arch.zip_file.name = zip_archive
    arch.save(update_fields=["zip_file"])
    url = reverse("download-file", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 403
    response = client_logged_in.get(f"{url}?password=secret")
    assert response.status_code == 200
