import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def auth_client(client: Client, django_user_model) -> Client:
    user = django_user_model.objects.create_user(username="testuser", password="testpass123")
    client.force_login(user)
    return client
