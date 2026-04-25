"""
Base models for RentTrack.

Every business entity inherits from TenantAwareModel to enforce
multi-tenant isolation at the ORM layer.
"""

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Adds created_at and updated_at to any model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Uses UUIDs as primary keys — safer for public APIs than sequential IDs."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TenantAwareModel(UUIDModel, TimeStampedModel):
    """
    Base class for all business models.

    Every row belongs to exactly one organization (tenant). The organization FK
    is used by RLS policies and by the TenantContextMiddleware to scope queries.
    """

    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        db_index=True,
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Adds soft-delete capability — records are never actually deleted."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])
