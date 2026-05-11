from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def error_403(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    return render(request, "base/403.html", status=403)


def error_404(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    return render(request, "base/404.html", status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    return render(request, "base/500.html", status=500)
