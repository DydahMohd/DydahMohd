from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import AuditLog, CustomUser, Ticket, TicketStatus, UserRole


def get_stale_tickets(days=3):
    cutoff = timezone.now() - timedelta(days=days)
    return Ticket.objects.filter(
        status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS],
        updated_at__lte=cutoff,
    ).select_related('reported_by', 'assigned_to'), cutoff


def send_stale_ticket_notification_emails(days=3):
    stale_tickets, cutoff = get_stale_tickets(days=days)
    if not stale_tickets.exists():
        return 0, 0

    admin_users = CustomUser.objects.filter(
        role=UserRole.ADMIN,
        is_active=True,
        email__isnull=False,
    ).exclude(email='')
    admin_emails = [user.email for user in admin_users]

    sent_count = 0
    recipient_count = 0

    for ticket in stale_tickets:
        recipients = set(admin_emails)
        if ticket.assigned_to and ticket.assigned_to.email:
            recipients.add(ticket.assigned_to.email)

        if not recipients:
            continue

        subject = f'EAC Helpdesk: Stale ticket alert - {ticket.title}'
        message = (
            f"Ticket #{ticket.pk} ('{ticket.title}') has been open or in progress since "
            f"{ticket.updated_at:%Y-%m-%d %H:%M}.\n\n"
            f"Status: {ticket.get_status_display()}\n"
            f"Priority: {ticket.get_priority_display()}\n"
            f"Reported by: {ticket.reported_by.get_full_name() or ticket.reported_by.username}\n"
            f"Assigned to: {ticket.assigned_to.get_full_name() if ticket.assigned_to else 'Unassigned'}\n"
            f"Wing: {ticket.wing or 'Not specified'}\n"
            f"Floor: {ticket.floor or 'Not specified'}\n"
            f"Room: {ticket.room_number or 'Not specified'}\n"
            f"Device: {ticket.device_serial_number or 'Not specified'}\n\n"
            f"Please review and update this ticket as soon as possible.\n"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(recipients),
            fail_silently=False,
        )

        AuditLog.objects.create(
            user=None,
            ticket=ticket,
            action_type='ticket_stale_notification',
            description=f'Stale ticket notification sent for ticket "{ticket.title}".',
            ip_address='',
            user_agent='',
            metadata={'recipients': list(recipients), 'cutoff': cutoff.isoformat()},
        )

        sent_count += 1
        recipient_count += len(recipients)

    return sent_count, recipient_count


def send_overdue_ticket_notification_emails():
    """
    Identifies tickets past their SLA deadline and notifies admins/technicians.
    """
    overdue_tickets = Ticket.objects.filter(
        status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS],
        due_at__lt=timezone.now(),
    ).select_related('reported_by', 'assigned_to')

    if not overdue_tickets.exists():
        return 0, 0

    admin_users = CustomUser.objects.filter(
        role=UserRole.ADMIN,
        is_active=True,
        email__isnull=False,
    ).exclude(email='')
    admin_emails = [user.email for user in admin_users]

    sent_count = 0
    recipient_count = 0

    for ticket in overdue_tickets:
        recipients = set(admin_emails)
        if ticket.assigned_to and ticket.assigned_to.email:
            recipients.add(ticket.assigned_to.email)

        if not recipients:
            continue

        subject = f'EAC Helpdesk: OVERDUE ticket alert - {ticket.title}'
        message = (
            f"Ticket #{ticket.pk} ('{ticket.title}') has exceeded its SLA deadline.\n\n"
            f"Deadline was: {ticket.due_at:%Y-%m-%d %H:%M}\n"
            f"Status: {ticket.get_status_display()}\n"
            f"Priority: {ticket.get_priority_display()}\n"
            f"Reported by: {ticket.reported_by.get_full_name() or ticket.reported_by.username}\n"
            f"Assigned to: {ticket.assigned_to.get_full_name() if ticket.assigned_to else 'Unassigned'}\n\n"
            f"Please take immediate action to resolve this incident.\n"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            list(recipients),
            fail_silently=False,
        )

        AuditLog.objects.create(
            user=None,
            ticket=ticket,
            action_type='ticket_overdue_notification',
            description=f'Overdue SLA notification sent for ticket "{ticket.title}".',
            metadata={'recipients': list(recipients), 'due_at': ticket.due_at.isoformat()},
        )

        sent_count += 1
        recipient_count += len(recipients)

    return sent_count, recipient_count


def predict_ticket_category(title: str, description: str) -> str:
    """
    Mocks an AI function to predict a ticket category based on title and description.
    In a real application, this would involve a trained NLP model.
    """
    text = (title + " " + description).lower()

    if any(keyword in text for keyword in ['printer', 'print', 'toner', 'paper jam']):
        return 'Printing'
    if any(keyword in text for keyword in ['network', 'wifi', 'internet', 'connection', 'router']):
        return 'Network'
    if any(keyword in text for keyword in ['software', 'application', 'program', 'excel', 'word', 'outlook']):
        return 'Software'
    if any(keyword in text for keyword in ['laptop', 'computer', 'monitor', 'keyboard', 'mouse', 'hardware', 'pc']):
        return 'Hardware'
    return 'General'
