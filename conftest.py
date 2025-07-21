import os
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from archives.models import Archive, FileItem
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture(autouse=True)
def override_media_root(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    settings.MEDIA_URL = "/"

@pytest.fixture
def user(db):
    return User.objects.create_user(username="u", password="p")

@pytest.fixture
def client_logged_in(client, user):
    client.force_login(user)
    setattr(client.handler, "_force_user", user)
    return client

@pytest.fixture
def archive(db, user):
    return Archive.objects.create(
        name="name", 
        short_code="c1",
        owner=user,
        ready=False,
        max_downloads=0,
    )

@pytest.fixture
def archive_with_password(db, user):
    return Archive.objects.create(
        name="name", 
        short_code="c1",
        owner=user,
        ready=False,
        max_downloads=0,
        password="secret",
    )

@pytest.fixture
def file_item(tmp_path, settings, archive):
    settings.MEDIA_ROOT = str(tmp_path)
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    f = SimpleUploadedFile("a.txt", b"data")
    return FileItem.objects.create(archive=archive, file=f)

@pytest.fixture
def api_client():
    return APIClient()
