from datetime import timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    CustomUser,
    Device,
    DeviceCondition,
    DeviceStatus,
    Ticket,
    TicketPriority,
    TicketStatus,
    UserRole,
)


class HelpdeskWorkflowTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass',
            role=UserRole.ADMIN,
        )
        self.tech = CustomUser.objects.create_user(
            username='tech',
            email='tech@example.com',
            password='pass',
            role=UserRole.TECHNICIAN,
        )
        self.staff = CustomUser.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='pass',
            role=UserRole.STAFF,
        )
        self.ticket = Ticket.objects.create(
            title='Printer failure',
            description='Printer in room 101 not working',
            reported_by=self.staff,
            priority=TicketPriority.HIGH,
            category='Hardware',
            wing='EACJ',
            floor='ground',
        )

    def test_admin_can_access_reports_but_staff_cannot(self):
        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('ticket_report'))
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('ticket_report'))
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_update_resolved_ticket(self):
        self.ticket.status = TicketStatus.RESOLVED
        self.ticket.save()

        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('ticket_update', kwargs={'pk': self.ticket.pk}))
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_comment_on_closed_ticket(self):
        self.ticket.status = TicketStatus.CLOSED
        self.ticket.save()

        self.client.login(username='staff', password='pass')
        response = self.client.post(
            reverse('ticket_comment', kwargs={'pk': self.ticket.pk}),
            {'comment': 'Please reopen this'},
        )
        self.assertEqual(response.status_code, 403)

    def test_reopen_ticket_workflow_records_reason_and_status(self):
        self.ticket.assigned_to = self.tech
        self.ticket.status = TicketStatus.RESOLVED
        self.ticket.save()

        self.client.login(username='tech', password='pass')
        response = self.client.post(
            reverse('ticket_reopen', kwargs={'pk': self.ticket.pk}),
            {'reason': 'Further investigation required'},
        )
        self.ticket.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.ticket.status, TicketStatus.IN_PROGRESS)
        self.assertEqual(self.ticket.reopen_reason, 'Further investigation required')
        self.assertIsNotNone(self.ticket.reopened_at)

    def test_stale_ticket_detection_and_notification(self):
        self.ticket.status = TicketStatus.OPEN
        self.ticket.save()
        Ticket.objects.filter(pk=self.ticket.pk).update(updated_at=timezone.now() - timedelta(days=4))
        self.ticket.refresh_from_db()

        self.assertTrue(self.ticket.is_stale)

        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('ticket_list') + '?stale=1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Printer failure')

        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            mail.outbox = []
            call_command('send_stale_ticket_notifications', '--days', '3')
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('Stale ticket alert', mail.outbox[0].subject)

    def test_device_audit_report_renders(self):
        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('device_audit_report'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Device Audit Report')
        self.assertContains(response, 'Total Devices')

    def test_device_audit_report_downloads(self):
        Device.objects.create(
            serial_number='EAC-DEVICE-001',
            name='Audit Laptop',
            status=DeviceStatus.OPERATIONAL,
            condition=DeviceCondition.GOOD,
            wing='EACJ',
            floor='ground',
            room_number='101',
        )
        self.client.login(username='admin', password='pass')

        downloads = [
            ('device_audit_report_pdf', 'application/pdf', 'device_audit_report.pdf'),
            (
                'device_audit_report_excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'device_audit_report.xlsx',
            ),
            ('device_audit_report_csv', 'text/csv', 'device_audit_report.csv'),
        ]

        for route_name, content_type, filename in downloads:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))

                self.assertEqual(response.status_code, 200)
                self.assertIn(content_type, response['Content-Type'])
                self.assertIn(filename, response['Content-Disposition'])
                self.assertGreater(len(response.content), 0)

        csv_response = self.client.get(reverse('device_audit_report_csv'))
        self.assertContains(csv_response, 'EAC-DEVICE-001')
