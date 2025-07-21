import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from archives.models.archive import Archive
from archives.models.file_item import FileItem

@pytest.fixture
def archive_data():
    return {
        "name": "api_test",
        "short_code": "API123",
        "max_downloads": 2,
        "expires_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
    }

@pytest.mark.django_db
def test_create_archive_api_requires_name(api_client, archive_data):
    data = dict(archive_data)
    del data["name"]
    url = reverse("archive-list")
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.json()

@pytest.mark.django_db
def test_create_archive_api_success(api_client, archive_data):
    url = reverse("archive-list")
    response = api_client.post(url, archive_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Archive.objects.filter(short_code="API123").exists()

@pytest.mark.django_db
def test_upload_file_to_archive_api(api_client, archive_data, tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    archive = Archive.objects.create(**archive_data)
    url = reverse("archive-detail", args=[archive.pk]) + "upload/"
    file_path = tmp_path / "f.txt"
    file_path.write_text("hello")
    with open(file_path, "rb") as fp:
        response = api_client.post(url, {"file": fp}, format="multipart")
    assert response.status_code == status.HTTP_201_CREATED
    assert FileItem.objects.filter(archive=archive).exists()
