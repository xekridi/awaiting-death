import os
import shutil
import pytest
from pathlib import Path

from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from archives.tasks import build_zip
from archives.models import Archive, FileItem

@pytest.fixture(autouse=True)
def setup_media(tmp_path, settings):
    m = tmp_path / "media"
    m.mkdir()
    settings.MEDIA_ROOT = str(m)
    yield

@pytest.fixture
def archive_with_files(db, tmp_path):
    arch = Archive.objects.create(
        name="name", 
        short_code="testcode",
        ready=False,
        owner=None,
    )
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"hello")
    fi = FileItem.objects.create(
        archive=arch,
        file=SimpleUploadedFile("a.txt", b"hello")
    )
    return arch

@pytest.fixture
def archive_ready(archive_with_files):
    filename = build_zip.run(archive_with_files.id)
    archive_with_files.refresh_from_db()
    assert archive_with_files.ready
    return archive_with_files

def test_build_zip_saved_in_zips(tmp_path, archive_with_files):
    settings.MEDIA_ROOT = str(tmp_path / "media")
    res = build_zip.run(archive_with_files.id)
    assert res.startswith("zips/")
    assert (Path(settings.MEDIA_ROOT) / res).exists()

@pytest.mark.django_db
def test_download_page_shows_preview(client, archive_ready):
    url = reverse("download-page", args=[archive_ready.short_code])
    resp = client.get(url)
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "<ul>" in content
    assert "Скачать" in content
    assert f'href="{reverse("download-file", args=[archive_ready.short_code])}"' in content

@pytest.mark.django_db
def test_download_file_success(client, archive_ready):
    url = reverse("download-file", args=[archive_ready.short_code])
    resp = client.get(url)
    assert resp.status_code == 200
    cd = resp["Content-Disposition"].lower()
    assert "attachment" in cd and ".zip" in cd

@pytest.mark.django_db
def test_download_file_password(client, archive_with_files, settings):
    arch = archive_with_files
    arch.password = "secret"
    arch.ready = True
    arch.zip_file.name = f"zips/{arch.short_code}.zip"
    arch.save(update_fields=["password", "ready", "zip_file"])
    zp = Path(settings.MEDIA_ROOT) / arch.zip_file.name
    zp.parent.mkdir()
    zp.write_bytes(b"zipdata")

    url = reverse("download-file", args=[arch.short_code])
    resp = client.get(url)
    assert resp.status_code == 403
    resp2 = client.get(url, {"password": "secret"})
    assert resp2.status_code == 200

@pytest.mark.django_db
def test_download_missing_file(client, archive_ready):
    arch = archive_ready
    os.remove(Path(settings.MEDIA_ROOT) / arch.zip_file.name)
    resp = client.get(reverse("download-file", args=[arch.short_code]))
    assert "Файл удалён" in resp.content.decode()
    assert resp.status_code == 200


@pytest.mark.django_db
def test_dashboard_delete_api(client_logged_in, user):
    arch = Archive.objects.create(
        short_code="delcode", owner=user, ready=True
    )
    url = reverse("archive-detail", args=[arch.id])
    resp = client_logged_in.delete(url)
    assert resp.status_code == 204
    with pytest.raises(Archive.DoesNotExist):
        Archive.objects.get(pk=arch.id)

@pytest.mark.django_db
def test_dashboard_content(client_logged_in, user):
    a1 = Archive.objects.create(short_code="c1", owner=user, ready=True)
    a2 = Archive.objects.create(short_code="c2", owner=user, ready=True)
    resp = client_logged_in.get(reverse("dashboard"))
    html = resp.content.decode()
    assert f'href="{reverse("download-page", args=[a1.short_code])}"' in html
    assert f'href="{reverse("download-page", args=[a2.short_code])}"' in html
    assert f'href="{reverse("stats", args=[a1.short_code])}"' in html
    assert f'href="{reverse("stats", args=[a2.short_code])}"' in html
    assert 'class="delete-arch"' in html
