from django.core.management.base import BaseCommand
from core.utils import send_overdue_ticket_notification_emails


class Command(BaseCommand):
    help = 'Send notification emails for tickets that have passed their SLA deadline.'

    def handle(self, *args, **options):
        sent_count, recipient_count = send_overdue_ticket_notification_emails()
        if sent_count:
            self.stdout.write(self.style.SUCCESS(
                f'Sent overdue alerts for {sent_count} ticket(s) to {recipient_count} recipient(s).'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('No overdue tickets found.'))