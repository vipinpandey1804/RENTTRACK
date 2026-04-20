"""
Payments: gateway integrations, reconciliation, and receipts.

Every payment is tied to a Bill and carries an immutable audit trail.
"""
from django.db import models

from apps.core.models import TenantAwareModel


class Payment(TenantAwareModel):
    """A payment made against one or more bills."""

    class Method(models.TextChoices):
        UPI = "upi", "UPI"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CARD = "card", "Card"
        CASH = "cash", "Cash"
        CHEQUE = "cheque", "Cheque"
        GATEWAY = "gateway", "Online Gateway"

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    bill = models.ForeignKey(
        "billing.Bill", on_delete=models.PROTECT, related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INITIATED
    )
    reference_number = models.CharField(max_length=100, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, blank=True, unique=True, null=True)

    # Gateway-specific
    gateway = models.CharField(max_length=30, blank=True, help_text="razorpay, stripe, etc.")
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)

    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recorded_payments"
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["bill", "status"]),
            models.Index(fields=["-paid_at"]),
        ]
        # Partitioning hint: partition by month(paid_at) in production

    def __str__(self):
        return f"{self.amount} for {self.bill.bill_number} ({self.status})"
