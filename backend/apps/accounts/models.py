"""
Accounts: Users, Organizations, Memberships, and Invites.

A single User can belong to multiple Organizations (e.g., a PMC employee
working for multiple property owners). Each membership carries a Role.
"""
import secrets
import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from apps.core.models import TimeStampedModel, UUIDModel


class Organization(UUIDModel, TimeStampedModel):
    """
    The tenant boundary. Every piece of business data belongs to an Organization.

    Tiers:
      - shared: Free/Pro (row-level isolation only)
      - pooled: Business (dedicated schema)
      - dedicated: Enterprise (dedicated DB instance)
    """

    class Tier(models.TextChoices):
        SHARED = "shared", "Shared (Free/Pro)"
        POOLED = "pooled", "Pooled (Business)"
        DEDICATED = "dedicated", "Dedicated (Enterprise)"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.SHARED)
    is_active = models.BooleanField(default=True)

    # Contact
    primary_email = models.EmailField()
    primary_phone = PhoneNumberField(blank=True)

    # Billing
    billing_address = models.TextField(blank=True)
    gstin = models.CharField(max_length=15, blank=True, help_text="Indian GST number")
    pan = models.CharField(max_length=10, blank=True)

    # Feature flags
    features = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "organizations"
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Custom manager — we use email, not username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser, UUIDModel):
    """Application user. Email is the unique identifier — no username."""

    username = None  # Remove username field from AbstractUser
    email = models.EmailField(unique=True, db_index=True)
    phone = PhoneNumberField(blank=True, db_index=True)
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    # The organization currently active in the UI. A user may belong to many.
    active_organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return self.email


class Membership(UUIDModel, TimeStampedModel):
    """
    Links a User to an Organization with a specific Role.

    A User can have multiple memberships. Within one organization a user
    has exactly one active role.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        PROPERTY_MANAGER = "property_manager", "Property Manager"
        ACCOUNTANT = "accountant", "Accountant"
        SUPPORT = "support", "Support Agent"
        TENANT = "tenant", "Tenant"
        CO_TENANT = "co_tenant", "Co-tenant"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "memberships"
        unique_together = [("user", "organization")]
        indexes = [
            models.Index(fields=["organization", "role"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.organization.name} ({self.role})"


class Invite(UUIDModel, TimeStampedModel):
    """
    Token-based invitation for a new or existing user to join an organization.

    Flow: owner creates Invite → email sent with link → tenant follows link
    → AcceptInviteView creates User + Membership, marks invite accepted.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invites"
    )
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sent_invites"
    )
    email = models.EmailField()
    role = models.CharField(max_length=32, choices=Membership.Role.choices)
    token = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Pre-assigned unit (optional — landlord may assign unit at invite time)
    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invites",
    )
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "invites"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["email", "organization"]),
        ]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.status == self.Status.PENDING and timezone.now() < self.expires_at

    def __str__(self):
        return f"Invite({self.email} → {self.organization.name})"
