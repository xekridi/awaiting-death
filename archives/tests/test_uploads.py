import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from celery.result import AsyncResult
from archives.models import Archive

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="u", password="p")

@pytest.fixture
def client_logged_in(client, user):
    client.force_login(user)
    return client

def test_wait_progress_redirects_if_not_authenticated(client):
    url = reverse("wait-progress", args=["nope"])
    response = client.get(url)
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]

def test_wait_progress_404_for_wrong_owner(client_logged_in, user):
    other = User.objects.create_user(username="other", password="p")
    arch = Archive.objects.create(
        short_code="abc", owner=other, ready=False
    )
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 404

def test_wait_progress_returns_working_if_no_task_and_no_error(client_logged_in, user):
    arch = Archive.objects.create(
        short_code="wrk", owner=user, ready=False, error=None, build_task_id=None
    )
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "working"}

def test_wait_progress_returns_ready_if_ready_flag_true(client_logged_in, user):
    arch = Archive.objects.create(
        short_code="rdy", owner=user, ready=True, error=None
    )
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_wait_progress_returns_error_if_model_error_set(client_logged_in, user):
    arch = Archive.objects.create(
        short_code="errm", owner=user, ready=False, error="boom!"
    )
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "error", "message": "boom!"}

def test_wait_progress_task_failed(monkeypatch, client_logged_in, user):
    arch = Archive.objects.create(
        short_code="tskf", owner=user, ready=False, error=None, build_task_id="tid1"
    )

    class DummyResult:
        def failed(self): return True
        @property
        def info(self): return {"exc": "task failure"}

    monkeypatch.setattr("archives.views_user.AsyncResult", lambda tid: DummyResult())

    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "error", "message": "task failure"}

def test_wait_progress_task_working(monkeypatch, client_logged_in, user):
    arch = Archive.objects.create(
        short_code="tskw", owner=user, ready=False, error=None, build_task_id="tid2"
    )

    class DummyResult:
        def failed(self): return False

    monkeypatch.setattr("archives.views_user.AsyncResult", lambda tid: DummyResult())

    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert response.json() == {"status": "working"}
