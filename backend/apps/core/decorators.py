from functools import wraps
from typing import Callable

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest


def role_required(*roles: str) -> Callable:
    """
    Restrict a view to users with one of the given roles.

    Usage:
        @role_required(User.Role.ADMIN, User.Role.MANAGER)
        def my_view(request): ...

    Superusers bypass the role check.
    """
    def decorator(view_func: Callable) -> Callable:
        @login_required
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator


def admin_required(view_func: Callable) -> Callable:
    """Shortcut: only ADMIN role (and superusers)."""
    return role_required("admin")(view_func)


def manager_required(view_func: Callable) -> Callable:
    """Shortcut: ADMIN or MANAGER role."""
    return role_required("admin", "manager")(view_func)
