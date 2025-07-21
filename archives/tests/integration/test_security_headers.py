import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_security_headers_present(client):
    response = client.get(reverse("home"))
    assert response["X-Frame-Options"] in ("DENY", "SAMEORIGIN")
    assert response["X-Content-Type-Options"] == "nosniff"
    csp = response.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
