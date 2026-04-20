"""
Properties: buildings, individual units within them, and leases.

Hierarchy: Organization → Property → Unit → Lease (with Tenant).
"""
from django.db import models
from django.utils import timezone

from apps.core.models import TenantAwareModel, SoftDeleteModel


class Property(TenantAwareModel, SoftDeleteModel):
    """A building or a standalone house owned by the organization."""

    class PropertyType(models.TextChoices):
        RESIDENTIAL = "residential", "Residential"
        COMMERCIAL = "commercial", "Commercial"
        MIXED = "mixed", "Mixed Use"

    name = models.CharField(max_length=200)
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.RESIDENTIAL
    )
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, default="IN")

    # Tariff defaults (can be overridden per unit)
    electricity_rate_per_unit = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Default per-unit rate in INR"
    )

    class Meta:
        db_table = "properties"
        verbose_name_plural = "Properties"
        indexes = [
            models.Index(fields=["organization", "is_deleted"]),
        ]

    def __str__(self):
        return self.name


class Unit(TenantAwareModel, SoftDeleteModel):
    """An individual rentable unit within a Property (flat, shop, room)."""

    class Status(models.TextChoices):
        VACANT = "vacant", "Vacant"
        OCCUPIED = "occupied", "Occupied"
        MAINTENANCE = "maintenance", "Under Maintenance"

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="units"
    )
    name = models.CharField(max_length=100, help_text="e.g., 'Flat 3B', 'Shop 2'")
    floor = models.IntegerField(null=True, blank=True)
    area_sqft = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    base_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    electricity_meter_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.VACANT)

    class Meta:
        db_table = "units"
        unique_together = [("property", "name")]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["property", "status"]),
        ]

    def __str__(self):
        return f"{self.property.name} / {self.name}"


class Lease(TenantAwareModel):
    """Tenancy agreement binding a tenant (User) to a Unit."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"
        TERMINATED = "terminated", "Terminated"

    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        YEARLY = "yearly", "Yearly"

    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="leases")
    tenant = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="leases"
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit_held = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_cycle = models.CharField(
        max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY
    )
    billing_day_of_month = models.IntegerField(
        default=1, help_text="Day of month when rent bill is generated (1–28)"
    )
    grace_period_days = models.IntegerField(default=5)
    late_fee_type = models.CharField(
        max_length=20,
        choices=[("flat", "Flat"), ("percentage", "Percentage"), ("none", "None")],
        default="none",
    )
    late_fee_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "leases"
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["unit", "status"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"{self.tenant.email} - {self.unit} ({self.status})"

    @property
    def is_active(self):
        today = timezone.now().date()
        return (
            self.status == self.Status.ACTIVE
            and self.start_date <= today
            and (self.end_date is None or self.end_date >= today)
        )
