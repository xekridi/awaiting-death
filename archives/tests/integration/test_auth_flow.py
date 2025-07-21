import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
def test_user_can_signup_and_redirect_to_dashboard(client):
    url = reverse("signup")
    response = client.post(url, {
        "username": "testuser",
        "password1": "pass12345",
        "password2": "pass12345",
    })
    assert response.status_code == 302
    assert reverse("dashboard") in response.url

@pytest.mark.django_db
def test_signup_password_mismatch_shows_error(client):
    url = reverse("signup")
    response = client.post(url, {
        "username": "user2",
        "password1": "abc",
        "password2": "xyz",
    })
    assert response.status_code == 200
    assert "password2" in response.context["form"].errors

@pytest.mark.django_db
def test_signup_duplicate_username_shows_error(client):
    User.objects.create_user(username="testdup", password="pass")
    url = reverse("signup")
    response = client.post(url, {
        "username": "testdup",
        "password1": "pass123",
        "password2": "pass123",
    })
    assert response.status_code == 200
    assert "username" in response.context["form"].errors

@pytest.mark.django_db
def test_user_can_login_and_access_dashboard(client):
    username = "loginuser"
    password = "testpass123"
    User.objects.create_user(username=username, password=password)
    login_url = reverse("login")
    response = client.post(login_url, {"username": username, "password": password})
    assert response.status_code == 302
    dash_response = client.get(reverse("dashboard"))
    assert dash_response.status_code == 200

@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302
    assert reverse("login") in response.url

@pytest.mark.django_db
def test_user_can_logout(client):
    username = "logoutuser"
    password = "logoutpass"
    User.objects.create_user(username=username, password=password)
    client.login(username=username, password=password)
    logout_url = reverse("logout")
    response = client.get(logout_url)
    assert response.status_code == 302
