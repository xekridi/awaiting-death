import pytest
from django.utils import timezone

from archives.models.archive import Archive
from archives.models.click_log import ClickLog
from archives.services.stats import get_downloads_by_day, get_top_referers


@pytest.mark.django_db
def test_get_downloads_by_day_and_top_referers():
    arch = Archive.objects.create(
        name="stats_test",
        short_code="STATS1",
        expires_at=timezone.now() + timezone.timedelta(days=1),
    )
    now = timezone.now()
    for _ in range(4):
        ClickLog.objects.create(archive=arch, timestamp=now, ip_address="1.1.1.1", referer="ref1")
    for _ in range(2):
        ClickLog.objects.create(archive=arch, timestamp=now - timezone.timedelta(days=1), ip_address="1.1.1.1", referer="")
    by_day = get_downloads_by_day("STATS1", days=2)
    assert any(count == 4 for _, count in by_day)
    assert any(count == 2 for _, count in by_day)
    top = get_top_referers("STATS1", limit=2)
    assert top[0] == ("ref1", 4)
    assert top[1] == ("direct", 2)
