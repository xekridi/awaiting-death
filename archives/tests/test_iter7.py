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


    def test_signup_and_login(self, client):
        signup_url = reverse('signup')
        response = client.get(signup_url)
        assert response.status_code == 200
        assert 'csrfmiddlewaretoken' in response.content.decode()

        response = client.post(signup_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'pass12345',
            'password2': 'pass12345',
        }, follow=True)
        assert response.status_code == 200
        assert User.objects.filter(username='testuser').exists()

        login_url = reverse('login')
        response = client.post(login_url, {
            'username': 'testuser',
            'password': 'pass12345',
        }, follow=True)
        assert response.status_code == 200
        dash_url = reverse('dashboard')
        response = client.get(dash_url)
        assert response.status_code == 200

    def test_upload_and_wait(self, client):
        url = reverse('upload')
        testfile = SimpleUploadedFile('f.txt', b'hello world')
        response = client.post(url, {
            'description': 'Desc',
            'files': testfile,
            'password1': '',
            'password2': '',
        }, format='multipart', follow=False)
        assert response.status_code == 302
        wait_url = response['Location']
        assert '/wait/' in wait_url
        response = client.get(wait_url)
        assert response.status_code == 200
        assert 'Ваш архив собирается' in response.content.decode()

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
        archive = Archive.objects.create(description='desc', short_code='st1', ready=True)
        url = reverse('stats', args=['st1'])
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'canvas' in content or 'Chart' in content

    def test_headers(self, client):
        response = client.get(reverse('home'))
        hdrs = response
        assert hdrs['X-Frame-Options'] in ('DENY', 'SAMEORIGIN')
        assert hdrs['X-Content-Type-Options'] == 'nosniff'
        assert 'Referrer-Policy' in hdrs
