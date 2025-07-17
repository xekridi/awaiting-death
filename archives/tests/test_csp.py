import pytest

@pytest.mark.django_db
def test_security_headers(client):
    resp = client.get("/")
    assert resp["X-Frame-Options"] == "DENY"
    assert resp["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in resp["Content-Security-Policy"]
