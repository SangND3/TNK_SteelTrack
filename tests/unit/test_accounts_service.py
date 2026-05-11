import pytest

from apps.accounts.models import User
from apps.core.exceptions import ApplicationError
from services.accounts import login_authenticate


@pytest.mark.django_db
class TestLoginAuthenticate:
    def test_valid_credentials_return_user(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="nhanvien01", password="MatKhau@123"
        )
        result = login_authenticate(username="nhanvien01", password="MatKhau@123")
        assert result.pk == user.pk

    def test_wrong_password_raises(self, django_user_model):
        django_user_model.objects.create_user(
            username="nhanvien02", password="MatKhau@123"
        )
        with pytest.raises(ApplicationError) as exc_info:
            login_authenticate(username="nhanvien02", password="SaiMatKhau")
        assert "không đúng" in str(exc_info.value)

    def test_nonexistent_user_raises(self):
        with pytest.raises(ApplicationError):
            login_authenticate(username="khong_ton_tai", password="any")

    def test_inactive_user_raises(self, django_user_model):
        django_user_model.objects.create_user(
            username="biquy", password="MatKhau@123", is_active=False
        )
        with pytest.raises(ApplicationError) as exc_info:
            login_authenticate(username="biquy", password="MatKhau@123")
        assert "khoá" in str(exc_info.value)


@pytest.mark.django_db
class TestUserRoleHelpers:
    def _make_user(self, role: str, **kwargs) -> User:
        return User.objects.create_user(
            username=f"user_{role}", password="x", role=role, **kwargs
        )

    def test_admin_is_admin(self):
        user = self._make_user(User.Role.ADMIN)
        assert user.is_admin is True
        assert user.is_manager is True
        assert user.is_viewer_only is False

    def test_manager_is_manager_not_admin(self):
        user = self._make_user(User.Role.MANAGER)
        assert user.is_admin is False
        assert user.is_manager is True
        assert user.is_viewer_only is False

    def test_staff_not_manager_not_viewer(self):
        user = self._make_user(User.Role.STAFF)
        assert user.is_admin is False
        assert user.is_manager is False
        assert user.is_viewer_only is False

    def test_viewer_is_viewer_only(self):
        user = self._make_user(User.Role.VIEWER)
        assert user.is_viewer_only is True
        assert user.is_manager is False

    def test_superuser_bypasses_all_role_checks(self):
        user = User.objects.create_superuser(
            username="god", password="x", role=User.Role.VIEWER
        )
        assert user.is_admin is True
        assert user.is_manager is True

    def test_has_role_single(self):
        user = self._make_user(User.Role.STAFF)
        assert user.has_role("staff") is True
        assert user.has_role("admin") is False

    def test_has_role_multiple(self):
        user = self._make_user(User.Role.MANAGER)
        assert user.has_role("admin", "manager") is True

    def test_role_badge_css_returns_string(self):
        for role in (User.Role.ADMIN, User.Role.MANAGER, User.Role.STAFF, User.Role.VIEWER):
            user = self._make_user(role)
            css = user.role_badge_css
            assert isinstance(css, str)
            assert len(css) > 0
