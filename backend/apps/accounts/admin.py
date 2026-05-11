from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "get_full_name", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)

    fieldsets = BaseUserAdmin.fieldsets + (  # type: ignore[operator]
        ("Thông tin hệ thống", {"fields": ("role", "phone", "avatar")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (  # type: ignore[operator]
        ("Thông tin hệ thống", {"fields": ("role", "phone")}),
    )
