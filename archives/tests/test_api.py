import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from archives.models import Archive, FileItem

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def archive_data():
    return {
        "short_code": "XYZ789",
        "max_downloads": 3,
        "expires_at": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
    }

@pytest.mark.django_db
def test_create_archive(api_client, archive_data):
    url = reverse("archive-list")
    resp = api_client.post(url, archive_data, format="json")
    assert resp.status_code == status.HTTP_201_CREATED
    assert Archive.objects.filter(short_code="XYZ789").exists()

@pytest.mark.django_db
def test_upload_file(api_client, archive_data, tmp_path, settings):
    archive = Archive.objects.create(**archive_data)
    url = reverse("archive-upload", args=[archive.pk])
    file_path = tmp_path / "f.txt"
    file_path.write_text("hello api")
    with open(file_path, "rb") as fp:
        resp = api_client.post(url, {"file": fp}, format="multipart")
    assert resp.status_code == status.HTTP_201_CREATED
    assert FileItem.objects.filter(archive=archive).exists()
