from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from apps.core.exceptions import ApplicationError
from services.accounts import login_authenticate

from .forms import LoginForm


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            user = login_authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
        except ApplicationError as exc:
            form.add_error(None, str(exc))
        else:
            login(request, user)
            # Session expiry: 2 weeks if "remember me", else browser session
            if not form.cleaned_data.get("remember_me"):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(60 * 60 * 24 * 14)

            next_url = request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("dashboard:index")

    ctx = {
        "form": form,
        "features": [
            "Quản lý tồn kho",
            "Theo dõi đơn hàng",
            "Báo cáo thống kê",
            "Phân quyền vai trò",
        ],
    }
    return render(request, "pages/accounts/login.html", ctx)


@require_http_methods(["POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Bạn đã đăng xuất thành công.")
    return redirect("accounts:login")


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/accounts/profile.html", {"user": request.user})
