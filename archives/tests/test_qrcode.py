import os
from django.urls import reverse
import pytest
from django.conf import settings
from archives.models import Archive

@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(username="u", password="p")

@pytest.mark.django_db
def test_qr_created_on_upload_form(client, tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    url = reverse("upload")
    with open(__file__, "rb") as f:
        resp = client.post(url, {
            "files": f,
            'name':'name',
        }, format="multipart")
    assert resp.status_code == 302
    code = resp["Location"].split("/")[2]
    arch = Archive.objects.get(short_code=code)
    assert arch.qr_image.name.startswith("qr_codes/")
    full_path = os.path.join(settings.MEDIA_ROOT, arch.qr_image.name)
    assert os.path.exists(full_path)

@pytest.mark.django_db
def test_qr_created_on_api_create(api_client, tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    data = {"short_code": "ZZZ", "max_downloads": 0}
    resp = api_client.post(reverse("archive-list"), data, format="json")
    assert resp.status_code == 201
    arch = Archive.objects.get(short_code="ZZZ")
    assert arch.qr_image.name.startswith("qr_codes/")
    assert os.path.exists(os.path.join(settings.MEDIA_ROOT, arch.qr_image.name))

@pytest.mark.django_db
def test_qr_visible_on_download_page(client, tmp_path, settings, user):
    settings.MEDIA_ROOT = str(tmp_path)
    arch = Archive.objects.create(
        name="name", 
        short_code="T1", 
        ready=True, 
        max_downloads=0, 
        owner=user
    )
    qr_dir = os.path.join(settings.MEDIA_ROOT, "qr_codes")
    os.makedirs(qr_dir, exist_ok=True)
    open(os.path.join(qr_dir, "T1.png"), "wb").close()
    arch.qr_image.name = "qr_codes/T1.png"
    arch.save(update_fields=["qr_image"])

    res = client.get(reverse("download-page", args=[arch.short_code]))
    assert f'<img src="{arch.qr_image.url}"' in res.content.decode()
