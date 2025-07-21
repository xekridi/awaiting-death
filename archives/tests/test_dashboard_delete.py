import pytest
from django.urls import reverse

from archives.models import Archive


def test_dashboard_delete(client_logged_in, archive):
    client_logged_in.force_login(archive.owner)
    _ = reverse("archive-detail", args=[archive.id])
    resp = client_logged_in.delete(reverse("archive-detail", args=[archive.id]))
    assert resp.status_code == 204
    with pytest.raises(Archive.DoesNotExist):
        Archive.objects.get(pk=archive.id)
