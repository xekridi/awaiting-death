import os
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture(autouse=True)
def override_media_root(settings):
    settings.MEDIA_ROOT = os.path.join(os.getcwd(), "test_media")

@pytest.fixture
def user(db):
    return User.objects.create_user(username="u", password="p")

@pytest.fixture
def client_logged_in(client, user):
    client.force_login(user)
    setattr(client.handler, "_force_user", user)
    return client
