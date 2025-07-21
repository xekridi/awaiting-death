import pytest
from django.contrib.auth import get_user_model
from accounts.forms import RegistrationForm
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

@pytest.mark.django_db
def test_registration_form_password_mismatch():
    form = RegistrationForm(data={
        "username": "foo",
        "email": "foo@example.com",
        "password1": "pass1",
        "password2": "pass2",
    })
    assert not form.is_valid()
    assert "password2" in form.errors

@pytest.mark.django_db
def test_registration_form_creates_user_with_valid_data():
    data = {
        "username": "bar",
        "email": "bar@example.com",
        "password1": "goodpass123",
        "password2": "goodpass123",
    }
    form = RegistrationForm(data=data)
    assert form.is_valid()
    user = form.save()
    assert User.objects.filter(pk=user.pk).exists()
    assert user.username == "bar"

@pytest.mark.django_db
def test_authentication_form_valid_credentials(user):
    form = AuthenticationForm(data={
        "username": user.username,
        "password": "p",
    })
    assert form.is_valid()

@pytest.mark.django_db
def test_authentication_form_invalid_credentials():
    form = AuthenticationForm(data={
        "username": "nouser",
        "password": "wrong",
    })
    assert not form.is_valid()
    assert "__all__" in form.errors
