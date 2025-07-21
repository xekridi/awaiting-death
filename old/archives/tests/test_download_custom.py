import zipfile

import pytest
from django.urls import reverse
from django.utils import timezone

from archives.models import Archive, ClickLog


@pytest.mark.django_db
def test_successful_download(tmp_path, client, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    zips = tmp_path / "zips"
    zips.mkdir()
    zip_path = zips / "ok.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        zf.writestr("f.txt", "data")
    arch = Archive.objects.create(
        name="name",
        short_code="DL1",
        ready=True,
        zip_file="zips/ok.zip"
    )
    url = reverse("download", args=["DL1"])
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp["Content-Disposition"].startswith("attachment")
    arch.refresh_from_db()
    assert arch.download_count == 1
    assert ClickLog.objects.filter(archive=arch).exists()


@pytest.mark.django_db
def test_limit_and_password(tmp_path, client, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    zips = tmp_path / "zips"
    zips.mkdir()
    zip_path = zips / "t.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        zf.writestr("a.txt", "x")
    exp = timezone.now() + timezone.timedelta(days=1)
    _ = Archive.objects.create(
        name="name",
        short_code="DL2",
        ready=True,
        zip_file="zips/t.zip",
        max_downloads=1,
        password="sec",
        expires_at=exp
    )
    url = reverse("download", args=["DL2"])
    resp = client.get(url)
    assert resp.status_code == 403
    resp = client.get(url + "?password=wrong")
    assert resp.status_code == 403
    resp = client.get(url + "?password=sec")
    assert resp.status_code == 200
    resp = client.get(url + "?password=sec")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_download_password(client, archive_with_password):
    response = client.post(f"/d/{archive_with_password.short_code}/", {"password": "secret"})
    assert response.status_code == 302
    response = client.get(f"/d/{archive_with_password.short_code}/")
    assert response.status_code == 302
