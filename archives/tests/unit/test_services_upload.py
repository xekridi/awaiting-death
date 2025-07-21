import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from archives.models.archive import Archive
from archives.models.file_item import FileItem
from archives.services.upload import handle_upload


@pytest.mark.django_db
def test_handle_upload_creates_archive_and_qr(tmp_path, settings, user):
    settings.MEDIA_ROOT = str(tmp_path)
    form_data = {
        "name": "My Archive",
        "description": "Description",
        "password1": "secret",
        "max_downloads": 5,
        "expires_at": None,
        "files": [SimpleUploadedFile("a.txt", b"data")],
    }
    request = RequestFactory().get("/")
    request.user = user
    archive = handle_upload(form_data, user, request)

    assert isinstance(archive, Archive)
    assert archive.password == "secret"
    assert os.path.exists(archive.qr_image.path)
    assert FileItem.objects.filter(archive=archive).count() == 1

@pytest.mark.django_db
def test_handle_upload_enqueues_task(monkeypatch, tmp_path, settings, user):
    settings.MEDIA_ROOT = str(tmp_path)
    called = {}

    def fake_apply_async(args):
        called["args"] = args
        class Result:
            id = "task-id"
        return Result()

    monkeypatch.setattr("archives.tasks.build_zip.apply_async", fake_apply_async)

    form_data = {
        "name": "X",
        "description": "",
        "password1": "",
        "max_downloads": 0,
        "expires_at": None,
        "files": [],
    }
    request = RequestFactory().get("/")
    request.user = user
    archive = handle_upload(form_data, user, request)

    assert called["args"] == (archive.id,)
    assert archive.build_task_id == "task-id"
