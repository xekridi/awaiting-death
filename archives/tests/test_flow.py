import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db
User = get_user_model()

def test_signup_login_upload_wait_flow(client):
    resp = client.post(reverse("signup"), {
        "username": "bob",
        "password1": "Qwe123456!",
        "password2": "Qwe123456!",
    })
    assert resp.status_code == 302
    assert resp["Location"].endswith("/dashboard/")

    client.login(username="bob", password="Qwe123456!")
    up_url = reverse("upload")
    response = client.post(
        up_url,
        {
            "description": "test",
            "files": SimpleUploadedFile("f.txt", b"hi"),
            "password1": "",
            "password2": "",
        },
        format="multipart",
        follow=False,
    )
    assert response.status_code == 302
    wait_url = response["Location"]
    assert "/wait/" in wait_url

    resp = client.get(wait_url)
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "<progress" in html and "wait-progress" in html and "const progressUrl" in html