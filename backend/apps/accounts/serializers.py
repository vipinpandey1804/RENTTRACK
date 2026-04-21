"""Serializers for accounts: signup, user profile, org, invite."""
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.models import Membership, Organization, User


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "tier", "primary_email", "primary_phone", "gstin", "pan"]
        read_only_fields = ["id", "slug", "tier"]


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organization", "role", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)
    active_organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "phone_verified",
            "email_verified",
            "active_organization",
            "memberships",
        ]
        read_only_fields = ["id", "email", "phone_verified", "email_verified"]


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, default="")
    org_name = serializers.CharField(max_length=200)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def save(self):
        data = self.validated_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        base_slug = slugify(data["org_name"])
        slug = base_slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization.objects.create(
            name=data["org_name"],
            slug=slug,
            primary_email=data["email"],
        )
        Membership.objects.create(
            user=user,
            organization=org,
            role=Membership.Role.OWNER,
        )
        user.active_organization = org
        user.save(update_fields=["active_organization"])
        return user


class InviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Membership.Role.choices)
    unit_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_role(self, value):
        if value == Membership.Role.OWNER:
            raise serializers.ValidationError("Cannot invite users as owners.")
        return value


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.CharField()
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")
    password = serializers.CharField(write_only=True, min_length=10, required=False)

    def validate(self, attrs):
        from apps.accounts.models import User

        # Password is required only if the user does not already exist
        email_from_token = self._get_email_for_token(attrs.get("token", ""))
        if email_from_token:
            if not User.objects.filter(email=email_from_token).exists():
                if not attrs.get("password"):
                    raise serializers.ValidationError(
                        {"password": "Password is required for new accounts."}
                    )
                validate_password(attrs["password"])
        return attrs

    def _get_email_for_token(self, token: str) -> str | None:
        from apps.accounts.models import Invite

        invite = Invite.objects.filter(token=token).first()
        return invite.email if invite else None


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_new_password(self, value):
        validate_password(value)
        return value
