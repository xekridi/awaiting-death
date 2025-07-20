import pytest
from django.urls import reverse
from celery.result import AsyncResult

from archives.models import Archive

@pytest.fixture
def archive_not_ready(db):
    return Archive.objects.create(
        short_code="unready",
        ready=False,
        error=None,
        build_task_id=None
    )

@pytest.fixture(autouse=True)
def patch_asyncresult(monkeypatch):
    class DummyResult:
        def __init__(self, info):
            self._info = info
        @property
        def info(self):
            return self._info

    monkeypatch.setattr(
        "archives.views_user.AsyncResult",
        lambda tid: DummyResult({"pct": 42})
    )

pytestmark = pytest.mark.django_db

class DummyResult:
    def __init__(self, info):
        self._info = info
    @property
    def info(self):
        return self._info

def test_wait_progress_returns_pct(client, archive_not_ready):
    url = reverse("wait-progress", args=[archive_not_ready.short_code])
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {"pct": 0}
