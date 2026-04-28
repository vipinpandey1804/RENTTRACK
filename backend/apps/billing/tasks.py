"""Background tasks for billing."""

import logging
import os
from datetime import date

from django.conf import settings

logger = logging.getLogger(__name__)


def generate_daily_bills():
    """Daily cron: generate rent bills for all active leases due today."""
    from django_q.tasks import async_task

    from apps.billing.services import generate_rent_bill, get_active_leases_due_today

    today = date.today()
    leases = get_active_leases_due_today()
    generated = 0
    errors = 0

    for lease in leases:
        try:
            bill = generate_rent_bill(lease, today)
            async_task("apps.notifications.tasks.notify_bill_issued", str(bill.id))
            async_task("apps.billing.tasks.generate_bill_pdf_task", str(bill.id))
            generated += 1
        except Exception as exc:
            logger.exception("Failed to generate bill for lease %s: %s", lease.id, exc)
            errors += 1

    logger.info(
        "generate_daily_bills: %d generated, %d errors (total leases due: %d)",
        generated,
        errors,
        len(leases),
    )
    return {"generated": generated, "errors": errors}


def mark_overdue_bills_task():
    """Daily cron: mark ISSUED bills past their due date as OVERDUE."""
    from apps.billing.services import mark_overdue_bills

    count = mark_overdue_bills()
    logger.info("mark_overdue_bills_task: %d bills marked overdue", count)
    return {"marked_overdue": count}


def generate_bill_pdf_task(bill_id: str) -> dict:
    """Async task: generate PDF for a bill and save it to media storage."""
    from apps.billing.models import Bill
    from apps.billing.pdf import generate_bill_pdf

    try:
        bill = (
            Bill.objects.select_related(
                "lease__tenant",
                "lease__unit__property",
                "organization",
            )
            .prefetch_related("line_items")
            .get(id=bill_id)
        )
        pdf_bytes = generate_bill_pdf(bill)

        rel_path = f"bills/{bill_id}.pdf"
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, "wb") as f:
            f.write(pdf_bytes)

        pdf_url = f"{settings.MEDIA_URL}{rel_path}"
        Bill.objects.filter(id=bill_id).update(pdf_url=pdf_url)
        logger.info("generate_bill_pdf_task: PDF generated for bill %s → %s", bill_id, pdf_url)
        return {"pdf_url": pdf_url}
    except Exception as exc:
        logger.exception("generate_bill_pdf_task failed for bill %s: %s", bill_id, exc)
        raise
