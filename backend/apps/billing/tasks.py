"""Celery tasks for billing."""
import logging
from datetime import date

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_daily_bills():
    """
    Daily cron: generate rent bills for all active leases due today.

    Scheduled via django-celery-beat (configure in admin or via data migration).
    Safe to re-run — generate_rent_bill is idempotent.
    """
    from apps.billing.services import generate_rent_bill, get_active_leases_due_today
    from apps.notifications.tasks import notify_bill_issued

    today = date.today()
    leases = get_active_leases_due_today()
    generated = 0
    errors = 0

    for lease in leases:
        try:
            bill = generate_rent_bill(lease, today)
            notify_bill_issued.delay(str(bill.id))
            generated += 1
        except Exception as exc:
            logger.exception("Failed to generate bill for lease %s: %s", lease.id, exc)
            errors += 1

    logger.info(
        "generate_daily_bills: %d generated, %d errors (total leases due: %d)",
        generated, errors, len(leases),
    )
    return {"generated": generated, "errors": errors}


@shared_task
def mark_overdue_bills_task():
    """
    Daily cron: mark ISSUED bills past their due date as OVERDUE.
    """
    from apps.billing.services import mark_overdue_bills

    count = mark_overdue_bills()
    logger.info("mark_overdue_bills_task: %d bills marked overdue", count)
    return {"marked_overdue": count}
