import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from archives.models import Archive

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="u", password="p")

@pytest.fixture
def client_logged_in(client, user):
    client.force_login(user)
    return client

@pytest.mark.django_db
class TestWaitProgress:
    def test_wait_progress_redirects_if_not_authenticated(self, client):
        url = reverse("wait-progress", args=["nope"])
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_wait_progress_404_for_wrong_owner(self, client_logged_in, user):
        other = User.objects.create_user(username="other", password="p")
        arch = Archive.objects.create(
            name="name",
            short_code="abc",
            owner=other,
            ready=False
        )
        url = reverse("wait-progress", args=[arch.short_code])
        response = client_logged_in.get(url)
        assert response.status_code == 404

    def test_wait_progress_returns_working_if_no_task_no_error(self, client_logged_in, user):
        arch = Archive.objects.create(
            name="name",
            short_code="wrk",
            owner=user,
            ready=False,
            error=None,
            build_task_id=None
        )
        url = reverse("wait-progress", args=[arch.short_code])
        resp = client_logged_in.get(url)
        assert resp.status_code == 200
        assert resp.json() == {"state": "PENDING", "pct": 0}

    def test_wait_progress_returns_ready_if_ready_flag(self, client_logged_in, user):
        arch = Archive.objects.create(
            name="name",
            short_code="rdy",
            owner=user,
            ready=True,
            error=None
        )
        url = reverse("wait-progress", args=[arch.short_code])
        resp = client_logged_in.get(url)
        assert resp.status_code == 200
        assert resp.json() == {
            "state": "SUCCESS",
            "pct": 100,
            "url": arch.get_download_url(),
        }

    def test_wait_progress_returns_error_if_model_error(self, client_logged_in, user):
        arch = Archive.objects.create(
            name="name",
            short_code="errm",
            owner=user,
            ready=False,
            error="boom!"
        )
        url = reverse("wait-progress", args=[arch.short_code])
        resp = client_logged_in.get(url)
        assert resp.status_code == 200
        assert resp.json() == {
            "state": "FAILURE",
            "pct": 0,
            "message": "boom!",
        }

    def test_wait_progress_task_failed(self, monkeypatch, client_logged_in, user):
        arch = Archive.objects.create(
            name="name",
            short_code="tskf",
            owner=user,
            ready=False,
            error=None,
            build_task_id="tid1"
        )

        class DummyResult:
            state = "FAILURE"
            info = {"exc": "task failure"}
            def failed(self):
                return True

        monkeypatch.setattr(
            "archives.views_user.AsyncResult",
            lambda tid: DummyResult()
        )

        url = reverse("wait-progress", args=[arch.short_code])
        resp = client_logged_in.get(url)
        assert resp.status_code == 200
        assert resp.json() == {'pct': 0, 'state': 'FAILURE'}

    def test_wait_progress_task_working(self, monkeypatch, client_logged_in, user):
        arch = Archive.objects.create(
            name="name",
            short_code="tskw",
            owner=user,
            ready=False,
            error=None,
            build_task_id="tid2"
        )

        class DummyResult:
            state = "PROGRESS"
            info = {"pct": 42}
            def failed(self):
                return False

        monkeypatch.setattr(
            "archives.views_user.AsyncResult",
            lambda tid: DummyResult()
        )

        url = reverse("wait-progress", args=[arch.short_code])
        resp = client_logged_in.get(url)
        assert resp.status_code == 200
        assert resp.json() == {"state": "PROGRESS", "pct": 42}
