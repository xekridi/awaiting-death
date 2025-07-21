import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_upload_redirects_to_wait_page(client_logged_in):
    url = reverse("upload")
    data = {
        "name": "Test Archive",
        "description": "A test",
        "password1": "",
        "max_downloads": 0,
        "expires_at": "",
        "files": [SimpleUploadedFile("file.txt", b"content")],
    }
    response = client_logged_in.post(url, data, format="multipart")
    assert response.status_code == 302
    assert reverse("wait", args=[response.url.strip("/").split("/")[-1]]) in response.url

@pytest.mark.django_db
def test_upload_and_wait_flow_shows_progress(client_logged_in, archive):
    url = reverse("wait", args=[archive.short_code])
    response = client_logged_in.get(url)
    content = response.content.decode()
    assert "Пожалуйста, подождите" in content or "Waiting" in content
