"""Auth and accounts API views."""
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, User
from apps.accounts.permissions import IsOrgOwner
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    InviteSerializer,
    MembershipSerializer,
    SignupSerializer,
    UserSerializer,
)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


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
    """Invite a user to the org. Owner-only."""
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

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        # Get or create user
        user, created = User.objects.get_or_create(
            email__iexact=email,
            defaults={"email": email},
        )

        membership, m_created = Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={"role": role},
        )
        if not m_created:
            if membership.is_active:
                return Response(
                    {"detail": "User is already a member of this organization."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            membership.role = role
            membership.is_active = True
            membership.save(update_fields=["role", "is_active"])

        # TODO: send invite email via Celery task
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


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
