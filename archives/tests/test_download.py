import os
import pytest
import zipfile
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from archives.models import Archive, ClickLog

@pytest.mark.django_db
def test_successful_download(tmp_path, client):
    exp = timezone.now() + timezone.timedelta(days=1)
    arch = Archive.objects.create(
        name="name", 
        short_code="DL1",
        expires_at=exp,
        ready=True,
        zip_file="zips/test.zip"
    )
    zdir = tmp_path / "zips"
    zdir.mkdir()
    zip_path = zdir / "test.zip"
    zip_path.write_bytes(b"PK\x05\x06")
    settings.MEDIA_ROOT = str(tmp_path)
    url = reverse("download", args=["DL1"])
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp["Content-Disposition"].startswith("attachment")
    assert Archive.objects.get(pk=arch.pk).download_count == 1
    assert ClickLog.objects.filter(archive=arch).count() == 1

@pytest.mark.django_db
def test_limit_and_password(tmp_path, client):
    exp = timezone.now() + timezone.timedelta(days=1)
    arch = Archive.objects.create(
        name="name", 
        short_code="DL2",
        expires_at=exp,
        ready=True,
        max_downloads=1,
        password="sec",
        zip_file="zips/t.zip"
    )
    settings.MEDIA_ROOT = str(tmp_path)
    resp = client.get(reverse("download", args=["DL2"]))
    assert resp.status_code == 403
    resp = client.get(f"{reverse('download', args=['DL2'])}?password=wrong")
    assert resp.status_code == 403
    (tmp_path / "zips").mkdir()
    (tmp_path / "zips" / "t.zip").write_bytes(b"PK\x05\x06")
    resp = client.get(f"{reverse('download', args=['DL2'])}?password=sec")
    assert resp.status_code == 200
    resp = client.get(f"{reverse('download', args=['DL2'])}?password=sec")
    assert resp.status_code == 403
