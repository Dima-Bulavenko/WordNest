from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import User


class UserAdmin(DefaultUserAdmin):
    ordering = ("email",)
    list_display = ("email", "date_joined", "is_superuser", "is_active")
    list_filter = ("is_superuser",)


admin.site.register(User, UserAdmin)
