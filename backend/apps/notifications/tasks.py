"""Celery tasks for notification dispatch."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_bill_issued(self, bill_id: str):
    """Async: send 'bill issued' email to the tenant."""
    try:
        from apps.billing.models import Bill
        from apps.notifications.services import notify_bill_issued_sync

        bill = Bill.objects.select_related(
            "lease__tenant", "lease__unit__property", "organization"
        ).get(id=bill_id)
        notify_bill_issued_sync(bill)
    except Exception as exc:
        logger.exception("notify_bill_issued failed for bill %s: %s", bill_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_payment_received(self, payment_id: str):
    """Async: send 'payment received' email to the tenant."""
    try:
        from apps.payments.models import Payment
        from apps.notifications.services import notify_payment_received_sync

        payment = Payment.objects.select_related(
            "bill__lease__tenant", "bill__organization"
        ).get(id=payment_id)
        notify_payment_received_sync(payment)
    except Exception as exc:
        logger.exception("notify_payment_received failed for payment %s: %s", payment_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1)
def dispatch_notification(self, notification_id: str):
    """Dispatch a queued Notification record."""
    try:
        from apps.notifications.models import Notification
        from apps.notifications.services import send_email

        notification = Notification.objects.select_related("recipient", "organization").get(
            id=notification_id
        )
        if notification.channel == Notification.Channel.EMAIL:
            send_email(notification)
        else:
            logger.warning(
                "dispatch_notification: channel %s not yet supported", notification.channel
            )
    except Exception as exc:
        logger.exception("dispatch_notification failed for %s: %s", notification_id, exc)
        raise self.retry(exc=exc)
