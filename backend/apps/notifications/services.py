"""
Notification service — creates Notification records and dispatches email.

Phase 1: email only. SMS/WhatsApp added in Phase 2.
"""
import logging

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from apps.notifications.models import Notification

logger = logging.getLogger(__name__)

# ── Event type constants ───────────────────────────────────────────────────────

BILL_ISSUED = "bill.issued"
BILL_OVERDUE = "bill.overdue"
PAYMENT_RECEIVED = "payment.received"
INVITE_SENT = "invite.sent"
WELCOME = "user.welcome"
EMAIL_VERIFICATION = "user.email_verification"


def _create_notification(
    *,
    organization,
    recipient,
    channel: str,
    event_type: str,
    subject: str,
    body: str,
    payload: dict | None = None,
) -> Notification:
    return Notification.objects.create(
        organization=organization,
        recipient=recipient,
        channel=channel,
        event_type=event_type,
        subject=subject,
        body=body,
        payload=payload or {},
        status=Notification.Status.PENDING,
    )


def send_email(notification: Notification) -> bool:
    """
    Attempt to send a notification record via Django's email backend.
    Updates notification status to SENT or FAILED.
    Returns True on success.
    """
    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@renttrack.app")
        send_mail(
            subject=notification.subject,
            message=notification.body,
            from_email=from_email,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at"])
        return True
    except Exception as exc:
        logger.exception("Email send failed for notification %s: %s", notification.id, exc)
        notification.status = Notification.Status.FAILED
        notification.error_message = str(exc)
        notification.retry_count += 1
        notification.save(update_fields=["status", "error_message", "retry_count"])
        return False


def notify_bill_issued_sync(bill) -> Notification | None:
    """Create + send 'bill issued' email to the tenant synchronously (used in tests)."""
    lease = bill.lease
    tenant = lease.tenant
    subject = f"Rent bill for {bill.period_start.strftime('%B %Y')} — ₹{bill.total_amount}"
    body = (
        f"Dear {tenant.first_name or tenant.email},\n\n"
        f"Your rent bill for {bill.period_start.strftime('%B %Y')} has been generated.\n\n"
        f"Bill number : {bill.bill_number}\n"
        f"Amount      : ₹{bill.total_amount}\n"
        f"Due date    : {bill.due_date.strftime('%d %B %Y')}\n"
        f"Unit        : {lease.unit.name}, {lease.unit.property.name}\n\n"
        f"Please pay by the due date to avoid late fees.\n\n"
        f"— RentTrack"
    )
    notification = _create_notification(
        organization=bill.organization,
        recipient=tenant,
        channel=Notification.Channel.EMAIL,
        event_type=BILL_ISSUED,
        subject=subject,
        body=body,
        payload={"bill_id": str(bill.id), "bill_number": bill.bill_number},
    )
    send_email(notification)
    return notification


def send_verification_email(user, verification_url: str) -> bool:
    """Send an email-verification link to the newly registered user."""
    subject = "Verify your RentTrack email address"
    body = (
        f"Hi {user.first_name or user.email},\n\n"
        f"Please verify your email address by clicking the link below:\n\n"
        f"{verification_url}\n\n"
        f"This link expires in 24 hours.\n\n"
        f"If you did not sign up for RentTrack, you can safely ignore this email.\n\n"
        f"— RentTrack"
    )
    notification = _create_notification(
        organization=user.active_organization,
        recipient=user,
        channel=Notification.Channel.EMAIL,
        event_type=EMAIL_VERIFICATION,
        subject=subject,
        body=body,
        payload={"user_id": str(user.id)},
    )
    return send_email(notification)


def send_invite_email(invite, invite_url: str) -> bool:
    """Send an invite email to the invited address."""
    subject = f"You've been invited to join {invite.organization.name} on RentTrack"
    inviter = invite.invited_by
    inviter_name = (
        f"{inviter.first_name} {inviter.last_name}".strip() if inviter else "Your landlord"
    )
    body = (
        f"Hi,\n\n"
        f"{inviter_name} has invited you to join {invite.organization.name} on RentTrack "
        f"as {invite.get_role_display()}.\n\n"
        f"Click the link below to accept the invitation and create your account:\n\n"
        f"{invite_url}\n\n"
        f"This invitation expires in 7 days.\n\n"
        f"— RentTrack"
    )
    from django.core.mail import send_mail

    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@renttrack.app")
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[invite.email],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.exception("Invite email failed for invite %s: %s", invite.id, exc)
        return False


def notify_payment_received_sync(payment) -> Notification | None:
    """Create + send 'payment received' email to the tenant."""
    bill = payment.bill
    tenant = bill.lease.tenant
    subject = f"Payment of ₹{payment.amount} received — {bill.bill_number}"
    body = (
        f"Dear {tenant.first_name or tenant.email},\n\n"
        f"We have received your payment of ₹{payment.amount}.\n\n"
        f"Bill number   : {bill.bill_number}\n"
        f"Payment amount: ₹{payment.amount}\n"
        f"Balance due   : ₹{bill.balance_due}\n"
        f"Status        : {bill.get_status_display()}\n\n"
        f"Thank you!\n\n"
        f"— RentTrack"
    )
    notification = _create_notification(
        organization=bill.organization,
        recipient=tenant,
        channel=Notification.Channel.EMAIL,
        event_type=PAYMENT_RECEIVED,
        subject=subject,
        body=body,
        payload={"bill_id": str(bill.id), "payment_id": str(payment.id)},
    )
    send_email(notification)
    return notification
