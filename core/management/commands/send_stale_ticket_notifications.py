from django.core.management.base import BaseCommand

from core.utils import send_stale_ticket_notification_emails


class Command(BaseCommand):
    help = 'Send notification emails for stale tickets open or in progress longer than 3 days.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Number of days after which an open or in-progress ticket is considered stale.',
        )

    def handle(self, *args, **options):
        days = options['days']
        sent_count, recipient_count = send_stale_ticket_notification_emails(days=days)
        if sent_count:
            self.stdout.write(self.style.SUCCESS(f'Sent stale alerts for {sent_count} ticket(s) to {recipient_count} recipient(s).'))
        else:
            self.stdout.write(self.style.SUCCESS('No stale tickets found.'))
