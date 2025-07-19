import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestAuth:
    def test_signup_success(self, client):
        url = reverse("signup")
        resp = client.post(url, {
            "username": "testuser",
            "password1": "pass12345",
            "password2": "pass12345",
        })
        assert resp.status_code == 302
        assert User.objects.filter(username="testuser").exists()

    def test_signup_password_mismatch(self, client):
        url = reverse('signup')
        data = {
            'username': 'user2',
            'password1': 'abc',
            'password2': 'xyz',
        }
        resp = client.post(url, data)
        assert resp.status_code == 200
        assert 'password2' in resp.context['form'].errors

    def test_signup_duplicate_username(self, client):
        User.objects.create_user(username='testdup', password='pass123')
        url = reverse('signup')
        data = {
            'username': 'testdup',
            'password1': 'pass123',
            'password2': 'pass123',
        }
        resp = client.post(url, data)
        assert resp.status_code == 200
        assert 'username' in resp.context['form'].errors

    def test_login_success_and_logout(self, client):
        User.objects.create_user(username="u1", password="pw1")
        login_url = reverse("login")
        resp = client.post(login_url, {
            "username": "u1",
            "password": "pw1",
        })
        assert resp.status_code == 302

        dash_url = reverse("dashboard")
        assert client.get(dash_url).status_code == 200

        logout_url = reverse("logout")
        resp = client.get(logout_url)
        assert resp.status_code == 302

    def test_login_invalid(self, client):
        login_url = reverse('login')
        resp = client.post(login_url, {
            'username': 'wrong',
            'password': 'wrong'
        })
        assert resp.status_code == 200
        assert resp.context['form'].non_field_errors()

    def test_dashboard_requires_login(self, client):
        url = reverse('dashboard')
        resp = client.get(url)
        assert resp.status_code == 302
        assert resp.url.startswith(reverse('login'))

    def test_signup_and_login(self, client):
        signup_url = reverse('signup')
        response = client.get(signup_url)
        assert response.status_code == 200
        assert 'csrfmiddlewaretoken' in response.content.decode()

        response = client.post(signup_url, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'pass12345',
            'password2': 'pass12345',
        }, follow=True)
        assert response.status_code == 200
        assert User.objects.filter(username='testuser').exists()

        login_url = reverse('login')
        response = client.post(login_url, {
            'username': 'testuser',
            'password': 'pass12345',
        }, follow=True)
        assert response.status_code == 200
        dash_url = reverse('dashboard')
        response = client.get(dash_url)
        assert response.status_code == 200