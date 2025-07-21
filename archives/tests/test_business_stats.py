import pytest
from django.utils import timezone
from archives.business.stats import get_downloads_by_day, get_top_referers
from archives.models import Archive, ClickLog

@pytest.mark.django_db
def test_downloads_by_day_and_top_referers():
    arch = Archive.objects.create(name="name", short_code="S1", expires_at=timezone.now() + timezone.timedelta(days=1))
    now = timezone.now()
    for _ in range(3):
        ClickLog.objects.create(archive=arch, timestamp=now, ip_address="1.1.1.1", referer="a")
    for _ in range(2):
        ClickLog.objects.create(archive=arch, timestamp=now - timezone.timedelta(days=1), ip_address="1.1.1.1", referer="")
    by_day = get_downloads_by_day("S1", days=2)
    assert any(cnt == 3 for _, cnt in by_day)
    assert any(cnt == 2 for _, cnt in by_day)
    top = get_top_referers("S1", limit=2)
    assert top[0] == ("a", 3)
    assert top[1] == ("direct", 2)
