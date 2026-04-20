"""RBAC permission classes for RentTrack."""
from rest_framework.permissions import BasePermission

from apps.accounts.models import Membership


class IsOrgMember(BasePermission):
    """Allows access if the user has an active membership in the org context."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org_id = getattr(request.user, "active_organization_id", None)
        if not org_id:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            is_active=True,
        ).exists()


class IsOrgOwner(BasePermission):
    """Allows access only to org owners."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org_id = getattr(request.user, "active_organization_id", None)
        if not org_id:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role=Membership.Role.OWNER,
            is_active=True,
        ).exists()


class IsOrgOwnerOrManager(BasePermission):
    """Allows owners and property managers."""

    ALLOWED_ROLES = {Membership.Role.OWNER, Membership.Role.PROPERTY_MANAGER}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org_id = getattr(request.user, "active_organization_id", None)
        if not org_id:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__in=self.ALLOWED_ROLES,
            is_active=True,
        ).exists()
