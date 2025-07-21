import os
import zipfile
import pytest
from django.urls import reverse
from django.utils import timezone
from archives.models import Archive, ClickLog

@pytest.fixture
def zip_path(settings, tmp_path):
    media_root = settings.MEDIA_ROOT
    os.makedirs(media_root, exist_ok=True)
    filename = "test_archive.zip"
    path = os.path.join(media_root, filename)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("file1.txt", "hello")
        zf.writestr("file2.txt", "world")
    return filename, ["file1.txt", "file2.txt"]

@pytest.mark.django_db
def test_preview_wait(client):
    arch = Archive.objects.create(
        short_code="wait1",
        ready=False,
        max_downloads=0,
    )
    url = reverse("download-page", args=["wait1"])
    resp = client.get(url)
    assert resp.status_code == 200
    assert "Пожалуйста, подождите" in resp.content.decode()

@pytest.mark.django_db
def test_preview_ready_list_files(client, zip_path):
    name, members = zip_path
    arch = Archive.objects.create(
        short_code="pr1",
        ready=True,
        max_downloads=0,
    )
    arch.zip_file.name = name
    arch.save(update_fields=["zip_file"])
    url = reverse("download-page", args=["pr1"])
    resp = client.get(url)
    content = resp.content.decode()
    assert resp.status_code == 200
    for m in members:
        assert m in content
    assert "Скачать" in content

@pytest.mark.django_db
def test_preview_missing_file(client):
    arch = Archive.objects.create(
        short_code="miss1",
        ready=True,
        max_downloads=0,
    )
    arch.zip_file.name = "no_such.zip"
    arch.save(update_fields=["zip_file"])
    url = reverse("download-page", args=["miss1"])
    resp = client.get(url)
    assert resp.status_code == 200
    assert "Файл удалён" in resp.content.decode()

@pytest.mark.django_db
def test_download_no_password(client, zip_path):
    name, _ = zip_path
    arch = Archive.objects.create(
        short_code="dl1",
        ready=True,
        max_downloads=0,
        password="secret"
    )
    arch.zip_file.name = name
    arch.save(update_fields=["zip_file"])
    url = reverse("download-file", args=["dl1"])
    resp = client.get(url)
    assert resp.status_code == 403

@pytest.mark.django_db
def test_download_with_password(client, zip_path):
    name, _ = zip_path
    arch = Archive.objects.create(
        short_code="dl2",
        ready=True,
        max_downloads=0,
        password="pw"
    )
    arch.zip_file.name = name
    arch.save(update_fields=["zip_file"])
    url = reverse("download-file", args=["dl2"])
    resp = client.get(f"{url}?password=pw")
    assert resp.status_code == 200
    assert "attachment" in resp["Content-Disposition"]
    arch.refresh_from_db()
    assert arch.download_count == 1
    assert ClickLog.objects.filter(archive=arch).exists()

@pytest.mark.django_db
def test_download_expired(client, zip_path):
    name, _ = zip_path
    arch = Archive.objects.create(
        short_code="dl3",
        ready=True,
        max_downloads=0,
        expires_at=timezone.now() - timezone.timedelta(hours=1)
    )
    arch.zip_file.name = name
    arch.save(update_fields=["zip_file"])
    url = reverse("download-file", args=["dl3"])
    resp = client.get(url)
    assert resp.status_code == 403

@pytest.mark.django_db
def test_download_limit(client, zip_path):
    name, _ = zip_path
    arch = Archive.objects.create(
        short_code="dl4",
        ready=True,
        max_downloads=1,
    )
    arch.zip_file.name = name
    arch.download_count = 1
    arch.save(update_fields=["zip_file", "download_count"])
    url = reverse("download-file", args=["dl4"])
    resp = client.get(url)
    assert resp.status_code == 403

