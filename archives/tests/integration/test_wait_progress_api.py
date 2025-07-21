import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from archives.models.archive import Archive

User = get_user_model()

@pytest.mark.django_db
def test_wait_progress_redirects_to_login_when_unauthenticated(client):
    url = reverse("wait-progress", args=["dummy"])
    response = client.get(url)
    assert response.status_code == 302
    assert reverse("login") in response["Location"]

@pytest.mark.django_db
def test_wait_progress_returns_404_for_non_owner(client_logged_in):
    other = User.objects.create_user(username="other", password="pass")
    arch = Archive.objects.create(short_code="CODE1", owner=other, ready=False)
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_wait_progress_pending_state(client_logged_in, user):
    arch = Archive.objects.create(short_code="CODE2", owner=user, ready=False, build_task_id=None, error=None)
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    assert response.json() == {"state": "PENDING", "pct": 0}

@pytest.mark.django_db
def test_wait_progress_success_state(client_logged_in, user):
    arch = Archive.objects.create(short_code="CODE3", owner=user, ready=True, error=None)
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    data = response.json()
    assert data["state"] == "SUCCESS"
    assert data["pct"] == 100
    assert "url" in data

@pytest.mark.django_db
def test_wait_progress_failure_state(client_logged_in, user):
    arch = Archive.objects.create(short_code="CODE4", owner=user, ready=False, error="failed", build_task_id=None)
    url = reverse("wait-progress", args=[arch.short_code])
    response = client_logged_in.get(url)
    data = response.json()
    assert data["state"] == "FAILURE"
    assert data["message"] == "failed"
    assert data["pct"] == 0
