"""Auth and accounts API views."""
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Invite, Membership, Organization, User
from apps.accounts.permissions import IsOrgOwner
from apps.accounts.serializers import (
    AcceptInviteSerializer,
    ChangePasswordSerializer,
    InviteSerializer,
    MembershipSerializer,
    SignupSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)

_VERIFICATION_TTL = 86_400  # 24 hours in seconds
_OTP_TTL = 600              # 10 minutes


def _verification_cache_key(token: str) -> str:
    return f"email_verification:{token}"


def _send_verification(user):
    """Generate a token, cache it, and dispatch the verification email."""
    import secrets
    token = secrets.token_urlsafe(32)
    cache.set(_verification_cache_key(token), str(user.id), _VERIFICATION_TTL)
    frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    verification_url = f"{frontend_base}/verify-email/{token}"
    try:
        from apps.notifications.services import send_verification_email
        send_verification_email(user, verification_url)
    except Exception:
        logger.exception("Failed to send verification email for user %s", user.id)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _send_verification(user)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """Consume a single-use email verification token."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token", "")
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        key = _verification_cache_key(token)
        user_id = cache.get(key)
        if not user_id:
            return Response(
                {"detail": "Invalid or expired verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.email_verified = True
        user.save(update_fields=["email_verified"])
        cache.delete(key)
        return Response({"detail": "Email verified successfully."})


class ResendVerificationView(APIView):
    """Re-send the email verification link for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.email_verified:
            return Response(
                {"detail": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST
            )
        _send_verification(user)
        return Response({"detail": "Verification email sent."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"current_password": ["Wrong password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class InviteView(APIView):
    """Create a token-based invite for a new tenant. Owner-only."""
    permission_classes = [IsAuthenticated, IsOrgOwner]

    @transaction.atomic
    def post(self, request):
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = request.user.active_organization
        if not org:
            return Response(
                {"detail": "No active organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower()
        role = serializer.validated_data["role"]
        unit_id = serializer.validated_data.get("unit_id")

        # Prevent duplicate pending invites
        existing = Invite.objects.filter(
            email=email,
            organization=org,
            status=Invite.Status.PENDING,
        ).first()
        if existing and existing.is_valid:
            return Response(
                {"detail": "A pending invite for this email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invite = Invite.objects.create(
            organization=org,
            invited_by=request.user,
            email=email,
            role=role,
            unit_id=unit_id,
        )

        frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        invite_url = f"{frontend_base}/accept-invite/{invite.token}"
        try:
            from apps.notifications.services import send_invite_email
            send_invite_email(invite, invite_url)
        except Exception:
            logger.exception("Failed to send invite email for invite %s", invite.id)

        return Response(
            {
                "id": str(invite.id),
                "email": invite.email,
                "role": invite.role,
                "status": invite.status,
                "expires_at": invite.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )


class ValidateInviteView(APIView):
    """Public: validate an invite token before showing the signup form."""
    permission_classes = [AllowAny]

    def get(self, request, token):
        invite = Invite.objects.select_related("organization").filter(token=token).first()
        if not invite or not invite.is_valid:
            return Response(
                {"detail": "Invalid or expired invitation."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                "email": invite.email,
                "role": invite.role,
                "organization": invite.organization.name,
                "expires_at": invite.expires_at,
            }
        )


class AcceptInviteView(APIView):
    """Public: complete signup via an invite token."""
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        invite = Invite.objects.select_related("organization").filter(token=token).first()
        if not invite or not invite.is_valid:
            return Response(
                {"detail": "Invalid or expired invitation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create or retrieve user
        user, created = User.objects.get_or_create(
            email=invite.email,
            defaults={
                "first_name": serializer.validated_data.get("first_name", ""),
                "last_name": serializer.validated_data.get("last_name", ""),
                "email_verified": True,
            },
        )
        if created:
            user.set_password(serializer.validated_data["password"])
            user.save(update_fields=["password", "first_name", "last_name", "email_verified"])
        elif not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])

        # Create membership
        membership, _ = Membership.objects.get_or_create(
            user=user,
            organization=invite.organization,
            defaults={"role": invite.role},
        )
        if not membership.is_active:
            membership.role = invite.role
            membership.is_active = True
            membership.save(update_fields=["role", "is_active"])

        # Set active org if not already set
        if not user.active_organization:
            user.active_organization = invite.organization
            user.save(update_fields=["active_organization"])

        # Mark invite accepted
        invite.status = Invite.Status.ACCEPTED
        invite.save(update_fields=["status"])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MembersView(APIView):
    """List all members of the current org."""
    permission_classes = [IsAuthenticated, IsOrgOwner]

    def get(self, request):
        org = request.user.active_organization
        if not org:
            return Response({"results": []})
        memberships = Membership.objects.filter(organization=org, is_active=True).select_related(
            "user", "organization"
        )
        return Response(MembershipSerializer(memberships, many=True).data)


class SwitchOrgView(APIView):
    """Switch the user's active organization."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org_id = request.data.get("organization_id")
        if not org_id:
            return Response(
                {"detail": "organization_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        membership = Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            is_active=True,
        ).first()
        if not membership:
            return Response(
                {"detail": "You are not a member of that organization."},
                status=status.HTTP_403_FORBIDDEN,
            )
        request.user.active_organization = membership.organization
        request.user.save(update_fields=["active_organization"])
        return Response(UserSerializer(request.user).data)
