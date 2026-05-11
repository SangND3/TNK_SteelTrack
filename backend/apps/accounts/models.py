from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user model with role-based access."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Quản trị viên"
        MANAGER = "manager", "Quản lý"
        STAFF = "staff", "Nhân viên"
        VIEWER = "viewer", "Xem"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    # ── Role helpers ──────────────────────────────────────────────────────────

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_manager(self) -> bool:
        return self.role in (self.Role.ADMIN, self.Role.MANAGER) or self.is_superuser

    @property
    def is_viewer_only(self) -> bool:
        return self.role == self.Role.VIEWER

    def has_role(self, *roles: str) -> bool:
        """Check if user has any of the given roles."""
        return self.role in roles or self.is_superuser

    @property
    def role_badge_css(self) -> str:
        """Tailwind CSS classes for the role badge in templates."""
        mapping = {
            self.Role.ADMIN: "bg-red-100 text-red-700",
            self.Role.MANAGER: "bg-blue-100 text-blue-700",
            self.Role.STAFF: "bg-green-100 text-green-700",
            self.Role.VIEWER: "bg-gray-100 text-gray-600",
        }
        return mapping.get(self.role, "bg-gray-100 text-gray-600")
