from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from ..models.click_log import ClickLog


def get_downloads_by_day(short_code, days=7):
    since = timezone.now() - timezone.timedelta(days=days)
    qs = (
        ClickLog.objects
        .filter(archive__short_code=short_code, timestamp__gte=since)
        .annotate(day=TruncDate("timestamp"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    return [(entry["day"].isoformat(), entry["count"]) for entry in qs]

def get_top_referers(short_code, limit=5):
    qs = (
        ClickLog.objects
        .filter(archive__short_code=short_code)
        .values("referer")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )
    return [(entry["referer"] or "direct", entry["count"]) for entry in qs]
