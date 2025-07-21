import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from archives.models import Archive, ClickLog


@pytest.mark.django_db
def test_archive_stats_api(client):
    Archive.objects.create(name="API", short_code="API1", expires_at=timezone.now() + timezone.timedelta(days=1))
    now = timezone.now()
    arch = Archive.objects.get(short_code="API1")
    ClickLog.objects.create(archive=arch, timestamp=now, ip_address="1.1.1.1", referer="r1")
    url = reverse("archive-stats", args=["API1"])
    resp = client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "by_day" in data and "top_referers" in data
    assert isinstance(data["by_day"], list)
    assert isinstance(data["top_referers"], list)
