# Feature map: Authentication & Authorization

## Status: ✅ Implemented (pre-MVP)

## Scope

- [x] Login / logout
- [x] Role-based access control (Admin / Manager / Staff / Viewer)
- [x] Session management (remember me, expiry)
- [ ] Password reset (not yet)
- [ ] 2FA (backlog)

## Where it lives

| Concern              | Location                                              |
| -------------------- | ----------------------------------------------------- |
| User model           | `backend/apps/accounts/models.py` — `User`            |
| Login form           | `backend/apps/accounts/forms.py` — `LoginForm`        |
| Auth service         | `backend/services/accounts.py` — `login_authenticate` |
| Role decorators      | `backend/apps/core/decorators.py`                     |
| Views                | `backend/apps/accounts/views.py`                      |
| URL patterns         | `backend/apps/accounts/urls.py` — `/accounts/`        |
| Login template       | `frontend/templates/pages/accounts/login.html`        |
| Profile template     | `frontend/templates/pages/accounts/profile.html`      |
| Role badge component | `frontend/templates/components/role_badge.html`       |
| Permission row       | `frontend/templates/components/permission_row.html`   |
| Sidebar (role-aware) | `frontend/templates/components/sidebar.html`          |
| 403 page             | `frontend/templates/base/403.html`                    |
| Error handlers       | `backend/apps/core/views.py`                          |
| Admin registration   | `backend/apps/accounts/admin.py`                      |
| Migration            | `backend/apps/accounts/migrations/0001_initial.py`    |
| Tests                | `tests/unit/test_accounts_service.py`                 |
|                      | `tests/unit/test_accounts_views.py`                   |

## Role matrix

| Feature              | Admin | Manager | Staff | Viewer |
| -------------------- | :---: | :-----: | :---: | :----: |
| Dashboard            |  ✅   |   ✅    |  ✅   |   ✅   |
| Xem kho thép         |  ✅   |   ✅    |  ✅   |   ✅   |
| Nhập/xuất kho        |  ✅   |   ✅    |  ✅   |   ❌   |
| Quản lý đơn hàng     |  ✅   |   ✅    |  ✅   |   ❌   |
| Xem báo cáo          |  ✅   |   ✅    |  ❌   |   ❌   |
| Django admin         |  ✅   |   ❌    |  ❌   |   ❌   |

## Key business rules

- Username + password auth (internal tool, không dùng email login)
- `remember_me=True` → session 14 ngày; `False` → browser session
- Inactive accounts (`is_active=False`) bị từ chối ngay tại service layer
- Superuser bypass tất cả role check
- Logout dùng POST (CSRF protection)
- 403 page hiển thị tên và role của user hiện tại

## Decorators usage

```python
from apps.core.decorators import role_required, admin_required, manager_required
from apps.accounts.models import User

@role_required(User.Role.ADMIN, User.Role.MANAGER)
def my_view(request): ...

@admin_required
def admin_only_view(request): ...

@manager_required
def manager_view(request): ...
```

## Branding

Login page dùng TNK brand:
- Xanh primary: `#0056A8` (tnk-blue)
- Cam accent:   `#F5821E` (tnk-orange)
- Xám bạc:     `#B0B4BA` (tnk-silver)
- Typeface: Inter (Google Fonts)
- SVG logo tái tạo từ `E:\Web\MyProject\branding\references\`
