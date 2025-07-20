import pytest
import uuid
import string

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

def test_get_upload_page(client):
    url = reverse("upload")
    resp = client.get(url)
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "<form" in html and 'enctype="multipart/form-data"' in html

def test_post_valid_upload_redirects_to_wait(client):
    url = reverse("upload")
    resp = client.post(
        url,
        {
            "description": "foo",
            "files": SimpleUploadedFile("a.txt", b"data"),
            "password1": "",
            "password2": "",
        },
        format="multipart",
    )
    assert resp.status_code == 302
    loc = resp["Location"]
    assert loc.startswith("/wait/")
    code = loc.split("/")[2]
    assert len(code) == 10 and all(c in string.hexdigits.lower() for c in code)