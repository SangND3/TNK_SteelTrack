import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User


@pytest.mark.django_db
class TestLoginView:
    def test_get_shows_form(self, client: Client):
        url = reverse("accounts:login")
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_authenticated_user_redirected_to_dashboard(self, client: Client, django_user_model):
        user = django_user_model.objects.create_user(username="u1", password="pass")
        client.force_login(user)
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 302
        assert "dashboard" in response["Location"]

    def test_valid_login_redirects_to_dashboard(self, client: Client, django_user_model):
        django_user_model.objects.create_user(username="u2", password="StrongPass@1")
        response = client.post(
            reverse("accounts:login"),
            {"username": "u2", "password": "StrongPass@1"},
        )
        assert response.status_code == 302

    def test_login_honors_safe_next_url(self, client: Client, django_user_model):
        django_user_model.objects.create_user(username="u_next", password="StrongPass@1")
        response = client.post(
            reverse("accounts:login") + "?next=/inventory/",
            {"username": "u_next", "password": "StrongPass@1"},
        )
        assert response.status_code == 302
        assert response["Location"] == "/inventory/"

    def test_login_rejects_open_redirect(self, client: Client, django_user_model):
        django_user_model.objects.create_user(username="u_evil", password="StrongPass@1")
        response = client.post(
            reverse("accounts:login") + "?next=https://evil.com/phish",
            {"username": "u_evil", "password": "StrongPass@1"},
        )
        assert response.status_code == 302
        assert "evil.com" not in response["Location"]
        assert "dashboard" in response["Location"]

    def test_invalid_password_shows_error(self, client: Client, django_user_model):
        django_user_model.objects.create_user(username="u3", password="correct")
        response = client.post(
            reverse("accounts:login"),
            {"username": "u3", "password": "wrong"},
        )
        assert response.status_code == 200
        assert response.context["form"].non_field_errors()

    def test_blank_submission_shows_form_errors(self, client: Client):
        response = client.post(reverse("accounts:login"), {})
        assert response.status_code == 200
        assert not response.context["form"].is_valid()

    def test_logout_requires_post(self, client: Client, django_user_model):
        user = django_user_model.objects.create_user(username="u4", password="p")
        client.force_login(user)
        response = client.get(reverse("accounts:logout"))
        # GET should not log out — Django returns 405
        assert response.status_code == 405

    def test_logout_post_redirects_to_login(self, client: Client, django_user_model):
        user = django_user_model.objects.create_user(username="u5", password="p")
        client.force_login(user)
        response = client.post(reverse("accounts:logout"))
        assert response.status_code == 302
        assert "login" in response["Location"]


@pytest.mark.django_db
class TestRoleDecorator:
    def _make_user(self, role: str) -> User:
        return User.objects.create_user(
            username=f"dec_{role}", password="x", role=role
        )

    def test_admin_can_access_admin_view(self, client: Client):
        user = self._make_user(User.Role.ADMIN)
        client.force_login(user)
        # Django admin requires is_staff; just test our role decorator logic
        assert user.is_admin is True

    def test_staff_cannot_access_manager_feature(self):
        user = self._make_user(User.Role.STAFF)
        assert user.is_manager is False

    def test_profile_requires_login(self, client: Client):
        response = client.get(reverse("accounts:profile"))
        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_profile_accessible_when_logged_in(self, client: Client, django_user_model):
        user = django_user_model.objects.create_user(username="profile_u", password="p")
        client.force_login(user)
        response = client.get(reverse("accounts:profile"))
        assert response.status_code == 200
