import io
import pytest
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from archives.models import Archive, FileItem, ClickLog

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="u", password="p")

@pytest.fixture
def client_logged_in(client, user):
    client.force_login(user)
    return client

@pytest.mark.django_db
class TestAuthFlows:

    def test_signup_success(self, client):
        url = reverse("signup")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "complex-pass-123",
            "password2": "complex-pass-123"
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert User.objects.filter(username="newuser").exists()

    def test_signup_duplicate_username(self, client):
        User.objects.create_user(username="dup", password="p")
        url = reverse("signup")
        data = {
            "username": "dup",
            "email": "dup@example.com",
            "password1": "pass1234",
            "password2": "pass1234"
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert "Пользователь с таким именем уже существует" in response.content.decode()

    def test_login_success(self, client, user):
        url = reverse("login")
        response = client.post(url, {"username": user.username, "password": "p"})
        assert response.status_code == 302
        assert int(client.session["_auth_user_id"]) == user.id

    def test_login_invalid(self, client):
        url = reverse("login")
        response = client.post(url, {"username": "nope", "password": "bad"})
        assert response.status_code == 200
        assert "Please enter a correct username and password" in response.content.decode()

@pytest.mark.django_db
class TestDownloadLimits:

    @pytest.fixture
    def arch_with_limit(self, tmp_path, user):
        a = Archive.objects.create(
            short_code="lim2",
            ready=True,
            max_downloads=2,
            expires_at=timezone.now() + timedelta(hours=1),
            owner=user
        )
        f = SimpleUploadedFile("f.txt", b"hello")
        FileItem.objects.create(archive=a, file=f)
        path = tmp_path / "zips" / "z1.zip"
        path.parent.mkdir()
        path.write_bytes(b"zipcontent")
        a.zip_file.name = f"zips/{path.name}"
        a.save(update_fields=["zip_file"])
        return a

    def test_download_within_limit(self, client_logged_in, arch_with_limit):
        url = reverse("download", args=[arch_with_limit.short_code])
        resp1 = client_logged_in.get(url)
        assert resp1.status_code == 200
        resp2 = client_logged_in.get(url)
        assert resp2.status_code == 200
        arch_with_limit.refresh_from_db()
        assert arch_with_limit.download_count == 2
        assert ClickLog.objects.filter(archive=arch_with_limit).count() == 2

    def test_download_exceeds_limit(self, client_logged_in, arch_with_limit):
        url = reverse("download", args=[arch_with_limit.short_code])
        client_logged_in.get(url)
        client_logged_in.get(url)
        resp3 = client_logged_in.get(url)
        assert resp3.status_code == 403

    def test_download_expired_archive(self, client_logged_in, tmp_path, user):
        a = Archive.objects.create(
            short_code="old",
            ready=True,
            max_downloads=0,
            expires_at=timezone.now() - timedelta(minutes=1),
            owner=user
        )
        f = SimpleUploadedFile("g.txt", b"data")
        FileItem.objects.create(archive=a, file=f)
        path = tmp_path / "zips" / "old.zip"
        path.parent.mkdir()
        path.write_bytes(b"zip")
        a.zip_file.name = f"zips/{path.name}"
        a.save(update_fields=["zip_file"])
        url = reverse("download", args=[a.short_code])
        resp = client_logged_in.get(url)
        assert resp.status_code == 404

@pytest.mark.django_db
def test_download_count_not_increment_when_forbidden(client_logged_in):
    a = Archive.objects.create(
        short_code="pwd",
        ready=True,
        max_downloads=0,
        password="secret",
        owner=client_logged_in.handler._force_user
    )
    a.zip_file.name = ""
    a.save()
    url = reverse("download", args=[a.short_code])
    resp = client_logged_in.get(url + "?password=wrong")
    assert resp.status_code == 403
    a.refresh_from_db()
    assert a.download_count == 0
