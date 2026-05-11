from django.contrib.auth import authenticate

from apps.accounts.models import User
from apps.core.exceptions import ApplicationError


def login_authenticate(*, username: str, password: str) -> User:
    """
    Verify credentials and return the User, or raise ApplicationError.

    Does NOT create or modify the Django session — that's the view's job.
    Keeps business logic testable without a request object.
    """
    user: User | None = authenticate(username=username, password=password)

    if user is None:
        raise ApplicationError("Tên đăng nhập hoặc mật khẩu không đúng.")

    if not user.is_active:
        raise ApplicationError("Tài khoản đã bị khoá. Liên hệ quản trị viên.")

    return user
