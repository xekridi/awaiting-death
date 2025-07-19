import io
import zipfile
import tempfile
from django.urls import reverse
from django.contrib.auth import get_user_model
import pytest
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from archives.models import Archive, FileItem

User = get_user_model()

@pytest.mark.django_db
class TestUIAndAccounts:
    def test_homepage_contains_buttons(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200
        html = response.content.decode("utf-8")
        assert "Загрузить архив" in html
        assert "Войти / Регистрация" in html

    def test_upload_and_wait(self, client):
        url = reverse('upload')
        testfile = SimpleUploadedFile('f.txt', b'hello world')
        response = client.post(
            url,
            {
                'description': 'Desc',
                'files': testfile,
                'password1': '',
                'password2': '',
            },
            format='multipart',
            follow=False,
        )
        assert response.status_code == 302
        wait_url = response['Location']
        assert '/wait/' in wait_url
        response = client.get(wait_url)
        assert response.status_code == 200

        content = response.content.decode('utf-8')
        assert 'const progressUrl' in content


    def test_download_view(self, client, settings, tmp_path):
        user = User.objects.create_user('u', 'u@example.com', 'pw')
        archive = Archive.objects.create(
            description='d',
            short_code='code123',
            ready=True,
            owner=user,
        )
        zip_path = tmp_path / 'z.zip'
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('file.txt', 'data')
        archive.zip_file.name = str(zip_path)
        archive.save(update_fields=['zip_file'])
        client.login(username='u', password='pw')
        url = reverse('download', args=['code123'])
        response = client.get(url)
        assert response.status_code == 200
        assert 'attachment' in response['Content-Disposition']

    def test_dashboard_access_and_content(self, client):
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        user = User.objects.create_user('u2', 'u2@example.com', 'pw')
        archive = Archive.objects.create(description='desc2', short_code='c2', owner=user)
        client.login(username='u2', password='pw')
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'desc2' in response.content.decode()

    def test_stats_page(self, client):
        user = User.objects.create_user("u3", "u3@example.com", "pw")
        archive = Archive.objects.create(
            description="desc", short_code="st1", ready=True, owner=user
        )

        resp = client.get(reverse("stats", args=["st1"]))
        assert resp.status_code == 302 and resp.url.startswith(reverse("login"))

        client.login(username="u3", password="pw")
        resp = client.get(reverse("stats", args=["st1"]))
        assert resp.status_code == 200
        assert "canvas" in resp.content.decode() or "Chart" in resp.content.decode()

    def test_headers(self, client):
        response = client.get(reverse('home'))
        hdrs = response
        assert hdrs['X-Frame-Options'] in ('DENY', 'SAMEORIGIN')
        assert hdrs['X-Content-Type-Options'] == 'nosniff'
        assert 'Referrer-Policy' in hdrs
