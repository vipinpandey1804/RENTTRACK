"""Background tasks for notification dispatch."""
import logging

logger = logging.getLogger(__name__)


def notify_bill_issued(bill_id: str):
    """Async: send 'bill issued' email to the tenant."""
    from apps.billing.models import Bill
    from apps.notifications.services import notify_bill_issued_sync

    bill = Bill.objects.select_related(
        "lease__tenant", "lease__unit__property", "organization"
    ).get(id=bill_id)
    notify_bill_issued_sync(bill)


def notify_payment_received(payment_id: str):
    """Async: send 'payment received' email to the tenant."""
    from apps.payments.models import Payment
    from apps.notifications.services import notify_payment_received_sync

    payment = Payment.objects.select_related(
        "bill__lease__tenant", "bill__organization"
    ).get(id=payment_id)
    notify_payment_received_sync(payment)


def dispatch_notification(notification_id: str):
    """Dispatch a queued Notification record."""
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
