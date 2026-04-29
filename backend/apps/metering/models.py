"""
Metering: meter readings and consumption tracking.

Readings flow: tenant submits -> optional OCR -> landlord confirms -> locked.
Once confirmed, a bill is generated from (current - previous) * rate.
"""

from django.db import models

from apps.core.models import TenantAwareModel


class MeterReading(TenantAwareModel):
    """A single meter reading for a unit in a given period."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted by Tenant"
        CONFIRMED = "confirmed", "Confirmed by Landlord"
        DISPUTED = "disputed", "Disputed"
        LOCKED = "locked", "Locked (billed)"

    class MeterType(models.TextChoices):
        ELECTRICITY = "electricity", "Electricity"
        WATER = "water", "Water"
        GAS = "gas", "Gas"

    unit = models.ForeignKey(
        "properties.Unit", on_delete=models.CASCADE, related_name="meter_readings"
    )
    meter_type = models.CharField(
        max_length=20, choices=MeterType.choices, default=MeterType.ELECTRICITY
    )
    period_month = models.DateField(help_text="First of the month this reading is for")
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2)
    current_reading = models.DecimalField(max_digits=10, decimal_places=2)
    units_consumed = models.DecimalField(max_digits=10, decimal_places=2)
    reading_photo_url = models.URLField(blank=True)
    ocr_extracted_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    submitted_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="submitted_readings"
    )
    confirmed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_readings",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "meter_readings"
        unique_together = [("unit", "meter_type", "period_month")]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["unit", "period_month"]),
        ]
        # Partitioning hint: in production, partition by month(period_month)

    def __str__(self):
        return f"{self.unit} {self.meter_type} {self.period_month}: {self.units_consumed}"

    def save(self, *args, **kwargs):
        self.units_consumed = self.current_reading - self.previous_reading
        super().save(*args, **kwargs)
