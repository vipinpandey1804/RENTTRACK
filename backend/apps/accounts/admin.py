"""Django admin configuration for the accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from apps.accounts.models import Invite, Membership, Organization, User


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ("organization", "role", "is_active")
    readonly_fields = ("organization",)
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email", "first_name", "last_name", "email_verified", "phone_verified",
        "active_organization", "is_staff", "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "email_verified", "phone_verified")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login", "password")

    fieldsets = (
        ("Identity", {"fields": ("id", "email", "first_name", "last_name")}),
        ("Contact", {"fields": ("phone", "phone_verified", "email_verified")}),
        ("Organization", {"fields": ("active_organization",)}),
        ("Access", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("date_joined", "last_login")}),
        ("Security", {"fields": ("password",), "classes": ("collapse",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )

    inlines = [MembershipInline]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "tier", "primary_email", "is_active", "created_at")
    list_filter = ("tier", "is_active")
    search_fields = ("name", "slug", "primary_email", "gstin", "pan")
    readonly_fields = ("id", "slug", "created_at", "updated_at", "features_display")
    ordering = ("-created_at",)

    fieldsets = (
        ("Identity", {"fields": ("id", "name", "slug", "tier", "is_active")}),
        ("Contact", {"fields": ("primary_email", "primary_phone")}),
        ("Billing", {"fields": ("billing_address", "gstin", "pan")}),
        ("Features", {"fields": ("features_display",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Feature flags")
    def features_display(self, obj):
        if not obj.features:
            return "—"
        import json
        return format_html("<pre style='margin:0'>{}</pre>", json.dumps(obj.features, indent=2))


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "is_active", "created_at")
    list_filter = ("role", "is_active", "organization")
    search_fields = ("user__email", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("user", "organization")
    ordering = ("-created_at",)


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("email", "organization", "role", "status", "invited_by", "expires_at", "created_at")
    list_filter = ("status", "role", "organization")
    search_fields = ("email", "organization__name", "invited_by__email")
    readonly_fields = ("id", "token", "created_at", "updated_at")
    raw_id_fields = ("organization", "invited_by", "unit")
    ordering = ("-created_at",)
