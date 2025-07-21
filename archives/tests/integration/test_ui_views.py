import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from archives.models.archive import Archive

User = get_user_model()

@pytest.mark.django_db
def test_homepage_shows_upload_and_auth_links(client):
    response = client.get(reverse("home"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Загрузить архив" in html
    assert "Войти" in html or "Регистрация" in html

@pytest.mark.django_db
def test_upload_and_wait_flow(client_logged_in):
    upload_url = reverse("upload")
    response = client_logged_in.post(
        upload_url,
        {
            "name": "UI Test",
            "description": "desc",
            "files": SimpleUploadedFile("u.txt", b"u"),
            "password1": "",
            "max_downloads": 0,
            "expires_at": "",
        },
        format="multipart",
    )
    assert response.status_code == 302
    wait_url = reverse("wait", args=[response.url.strip("/").split("/")[-1]])
    wait_resp = client_logged_in.get(wait_url)
    assert wait_resp.status_code == 200
    assert "Пожалуйста, подождите" in wait_resp.content.decode()

@pytest.mark.django_db
def test_dashboard_requires_login_and_displays_archives(client, user):
    archive = Archive.objects.create(short_code="dash1", owner=user, name="dash")
    dashboard_url = reverse("dashboard")
    resp = client.get(dashboard_url)
    assert resp.status_code == 302
    client.login(username=user.username, password="p")
    resp2 = client.get(dashboard_url)
    assert resp2.status_code == 200
    assert "dash" in resp2.content.decode()

@pytest.mark.django_db
def test_stats_page_requires_login_and_renders_chart(client, user):
    arch = Archive.objects.create(short_code="stat1", owner=user, ready=True, name="stats")
    stats_url = reverse("stats", args=[arch.short_code])
    resp = client.get(stats_url)
    assert resp.status_code == 302
    client.login(username=user.username, password="p")
    resp2 = client.get(stats_url)
    assert resp2.status_code == 200
    assert "<canvas" in resp2.content.decode()
