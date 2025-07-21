import pytest
from django.urls import reverse
from django.utils import timezone

from archives.models.click_log import ClickLog


@pytest.mark.django_db
def test_successful_file_download(tmp_path, client_logged_in, settings, archive):
    settings.MEDIA_ROOT = str(tmp_path)
    archive.ready = True
    archive.expires_at = timezone.now() + timezone.timedelta(days=1)
    archive.zip_file.name = f"{archive.short_code}.zip"
    archive.save(update_fields=["ready", "expires_at", "zip_file"])

    zip_path = tmp_path / archive.zip_file.name
    zip_path.write_bytes(b"zipdata")

    url = reverse("download", args=[archive.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    archive.refresh_from_db()
    assert archive.download_count == 1
    assert ClickLog.objects.filter(archive=archive).exists()

@pytest.mark.django_db
def test_download_forbidden_when_password_mismatch(client_logged_in, archive):
    archive.ready = True
    archive.password = "secret"
    archive.save(update_fields=["ready", "password"])

    url = reverse("download", args=[archive.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 403

    response = client_logged_in.get(f"{url}?password=wrong")
    assert response.status_code == 403

@pytest.mark.django_db
def test_download_success_when_password_correct(tmp_path, client_logged_in, settings, archive):
    settings.MEDIA_ROOT = str(tmp_path)
    archive.ready = True
    archive.password = "pw"
    archive.expires_at = timezone.now() + timezone.timedelta(days=1)
    archive.save(update_fields=["ready", "password", "expires_at"])

    filename = f"{archive.short_code}.zip"
    zip_path = tmp_path / filename
    zip_path.write_bytes(b"zipdata")
    archive.zip_file.name = filename
    archive.save(update_fields=["zip_file"])

    url = reverse("download", args=[archive.short_code])
    post_resp = client_logged_in.post(url, {"password": "pw"})
    assert post_resp.status_code == 302

    get_resp = client_logged_in.get(url)
    assert get_resp.status_code == 200

@pytest.mark.django_db
def test_download_forbidden_when_limit_exceeded(tmp_path, client_logged_in, settings, archive):
    settings.MEDIA_ROOT = str(tmp_path)
    archive.ready = True
    archive.max_downloads = 1
    archive.download_count = 1
    archive.save(update_fields=["ready", "max_downloads", "download_count"])

    url = reverse("download", args=[archive.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 403
