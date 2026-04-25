"""
Billing: invoices, line items, and payment tracking.

Bills are immutable once issued. Corrections happen via credit notes.
Payments are recorded against bills with full audit trail.
"""

from django.db import models

from apps.core.models import TenantAwareModel


class Bill(TenantAwareModel):
    """An invoice issued to a tenant for a specific billing period."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        PARTIALLY_PAID = "partially_paid", "Partially Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    class BillType(models.TextChoices):
        RENT = "rent", "Rent"
        ELECTRICITY = "electricity", "Electricity"
        WATER = "water", "Water"
        MAINTENANCE = "maintenance", "Maintenance"
        COMBINED = "combined", "Combined"

    lease = models.ForeignKey("properties.Lease", on_delete=models.PROTECT, related_name="bills")
    bill_number = models.CharField(max_length=50, unique=True)
    bill_type = models.CharField(max_length=20, choices=BillType.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    issue_date = models.DateField()
    due_date = models.DateField(db_index=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    pdf_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "bills"
        indexes = [
            models.Index(fields=["organization", "status", "due_date"]),
            models.Index(fields=["lease", "status"]),
        ]
        # Partitioning hint: in production, partition by month(issue_date)

    def __str__(self):
        return f"{self.bill_number} ({self.total_amount})"

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid


class BillLineItem(TenantAwareModel):
    """Individual line on a bill — rent, electricity, late fee, etc."""

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="line_items")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "bill_line_items"
