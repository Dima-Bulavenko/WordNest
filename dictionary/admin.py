from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from dictionary import models


class UserAdmin(DefaultUserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_superuser", "is_active")
    list_filter = ("is_superuser", "is_active")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_active",
                    "is_superuser",
                ),
            },
        ),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Language)
admin.site.register(models.Word)
admin.site.register(models.Translation)
admin.site.register(models.Dictionary)
