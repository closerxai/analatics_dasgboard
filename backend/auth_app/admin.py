from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CompanyMember, CustomUser, Invitation, JoinRequest, Role


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "phone_number", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name", "phone_number")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "phone_number", "password1", "password2"),
            },
        ),
    )


admin.site.register(Role)
admin.site.register(CompanyMember)
admin.site.register(Invitation)
admin.site.register(JoinRequest)
