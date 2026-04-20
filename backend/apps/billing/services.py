"""
Billing service layer.

All bill generation logic lives here so views and tasks stay thin.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.billing.models import Bill, BillLineItem
from apps.properties.models import Lease, Unit


def _month_range(period_date: date) -> tuple[date, date]:
    """Return (first_day, last_day) for the month containing period_date."""
    start = period_date.replace(day=1)
    # Last day = first day of next month minus one day
    next_month = (start + timedelta(days=32)).replace(day=1)
    end = next_month - timedelta(days=1)
    return start, end


def _due_date(issue_date: date, billing_day: int) -> date:
    """Return the due date in the same or next month depending on billing_day."""
    candidate = issue_date.replace(day=billing_day)
    if candidate < issue_date:
        next_month = (issue_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        candidate = next_month.replace(day=billing_day)
    return candidate


def _bill_number(organization) -> str:
    """Generate a unique, human-readable bill number."""
    prefix = organization.slug[:4].upper()
    suffix = uuid.uuid4().hex[:6].upper()
    month = timezone.now().strftime("%Y%m")
    return f"RT-{month}-{prefix}-{suffix}"


@transaction.atomic
def generate_rent_bill(lease: Lease, period_date: date) -> Bill:
    """
    Create a RENT bill for the given lease and month.

    Idempotent: returns existing bill if one already exists for this
    (lease, bill_type=RENT, period_start) combination.
    """
    period_start, period_end = _month_range(period_date)

    existing = Bill.objects.filter(
        lease=lease,
        bill_type=Bill.BillType.RENT,
        period_start=period_start,
    ).first()
    if existing:
        return existing

    today = timezone.now().date()
    issue_date = today
    due_date = _due_date(issue_date, lease.billing_day_of_month)

    rent = lease.monthly_rent
    late_fee = Decimal("0")

    bill = Bill.objects.create(
        organization=lease.organization,
        lease=lease,
        bill_number=_bill_number(lease.organization),
        bill_type=Bill.BillType.RENT,
        period_start=period_start,
        period_end=period_end,
        issue_date=issue_date,
        due_date=due_date,
        subtotal=rent,
        tax_amount=Decimal("0"),
        total_amount=rent,
        status=Bill.Status.ISSUED,
    )

    BillLineItem.objects.create(
        organization=lease.organization,
        bill=bill,
        description=f"Rent – {period_start.strftime('%B %Y')}",
        quantity=Decimal("1"),
        unit_price=rent,
        amount=rent,
    )

    return bill


@transaction.atomic
def apply_payment(bill: Bill, amount: Decimal, method: str, recorded_by, reference: str = "", notes: str = "") -> "Payment":  # noqa: F821
    """
    Record a manual payment against a bill and update its status.

    Raises ValueError if amount exceeds remaining balance.
    """
    from apps.payments.models import Payment

    balance = bill.balance_due
    if amount <= Decimal("0"):
        raise ValueError("Payment amount must be positive.")
    if amount > balance:
        raise ValueError(f"Payment amount {amount} exceeds balance due {balance}.")

    payment = Payment.objects.create(
        organization=bill.organization,
        bill=bill,
        amount=amount,
        method=method,
        status=Payment.Status.SUCCESS,
        reference_number=reference,
        recorded_by=recorded_by,
        paid_at=timezone.now(),
        notes=notes,
    )

    bill.amount_paid = (bill.amount_paid or Decimal("0")) + amount
    if bill.amount_paid >= bill.total_amount:
        bill.status = Bill.Status.PAID
    elif bill.amount_paid > Decimal("0"):
        bill.status = Bill.Status.PARTIALLY_PAID
    bill.save(update_fields=["amount_paid", "status"])

    # Fire async notification (import here to avoid circular at module level)
    from apps.notifications.tasks import notify_payment_received
    notify_payment_received.delay(str(payment.id))

    return payment


def mark_overdue_bills() -> int:
    """
    Set ISSUED bills past their due date to OVERDUE.
    Returns count of bills updated.
    """
    today = timezone.now().date()
    updated = Bill.objects.filter(
        status=Bill.Status.ISSUED,
        due_date__lt=today,
    ).update(status=Bill.Status.OVERDUE)
    return updated


def get_active_leases_due_today() -> list:
    """Return active leases whose billing_day_of_month matches today."""
    today = timezone.now().date()
    return list(
        Lease.objects.filter(
            status=Lease.Status.ACTIVE,
            billing_day_of_month=today.day,
            start_date__lte=today,
        ).select_related("organization", "unit", "tenant")
        .filter(end_date__isnull=True) | Lease.objects.filter(
            status=Lease.Status.ACTIVE,
            billing_day_of_month=today.day,
            start_date__lte=today,
            end_date__gte=today,
        ).select_related("organization", "unit", "tenant")
    )
