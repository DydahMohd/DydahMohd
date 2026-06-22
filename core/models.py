from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    TECHNICIAN = 'technician', 'Technician'
    STAFF = 'staff', 'Staff'
    PROPERTY_MANAGER = 'property_manager', 'Property Manager'


class TechnicianType(models.TextChoices):
    IT = 'it', 'IT Support'
    ELECTRICAL = 'electrical', 'Electrical / Power'
    PLUMBING = 'plumbing', 'Plumbing'
    MECHANICAL = 'mechanical', 'Mechanical / HVAC'
    ELECTRONICS = 'electronics', 'Electronics'
    OTHER = 'other', 'Other'


class TicketStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    IN_PROGRESS = 'in_progress', 'In Progress'
    RESOLVED = 'resolved', 'Resolved'
    CLOSED = 'closed', 'Closed'


class TicketPriority(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'

class MaterialRequestStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    ISSUED = 'issued', 'Issued / Delivered'
    CANCELLED = 'cancelled', 'Cancelled'


class ChangeRequestStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING = 'pending', 'Pending Approval'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    IMPLEMENTED = 'implemented', 'Implemented'
    CLOSED = 'closed', 'Closed'


class WingChoices(models.TextChoices):
    EACJ = 'EACJ', 'EACJ'
    SECRETARIAT = 'Secretariat', 'Secretariat'
    EALA = 'EALA', 'EALA'


class FloorChoices(models.TextChoices):
    GROUND = 'ground', 'Ground Floor'
    FIRST = 'first', 'First Floor'
    SECOND = 'second', 'Second Floor'
    THIRD = 'third', 'Third Floor'


class DeviceType(models.TextChoices):
    MONITOR = 'monitor', 'Monitor'
    UPS = 'ups', 'UPS'
    KEYBOARD = 'keyboard', 'Keyboard'
    MOUSE = 'mouse', 'Mouse'
    CPU = 'cpu', 'CPU'
    LAPTOP = 'laptop', 'Laptop'
    PRINTER = 'printer', 'Printer'
    SCANNER = 'scanner', 'Scanner'
    SERVER = 'server', 'Server'
    PROJECTOR = 'projector', 'Projector'
    IP_PHONE = 'ip_phone', 'IP Phone'
    TABLET = 'tablet', 'Tablet'
    CONFERENCE_SYSTEM = 'conference', 'Conference System'
    NETWORK_DEVICE = 'network', 'Network Device'
    OTHER = 'other', 'Other'


class DeviceStatus(models.TextChoices):
    OPERATIONAL = 'operational', 'Operational'
    MAINTENANCE_DUE = 'maintenance_due', 'Maintenance due'
    DECOMMISSIONED = 'decommissioned', 'Decommissioned'


class DeviceCondition(models.TextChoices):
    GOOD = 'good', 'Good'
    FAIR = 'fair', 'Fair'
    POOR = 'poor', 'Poor'


class Device(models.Model):
    serial_number = models.CharField(max_length=150)
    name = models.CharField(max_length=200, blank=True)
    device_type = models.CharField(
        max_length=50,
        choices=DeviceType.choices,
        default=DeviceType.OTHER,
    )
    assigned_user = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_devices',
        help_text="The staff member currently in possession of this device."
    )
    other_device_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specify the hardware type if 'Other' is selected."
    )
    wing = models.CharField(
        max_length=20,
        choices=WingChoices.choices,
        default=WingChoices.EACJ,
        blank=True,
    )
    floor = models.CharField(
        max_length=20,
        choices=FloorChoices.choices,
        blank=True,
    )
    room_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=DeviceStatus.choices,
        default=DeviceStatus.OPERATIONAL,
    )
    condition = models.CharField(
        max_length=20,
        choices=DeviceCondition.choices,
        default=DeviceCondition.GOOD,
    )
    last_inspected = models.DateField(null=True, blank=True)
    next_inspection = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'device'
        verbose_name_plural = 'devices'
        constraints = [
            models.UniqueConstraint(fields=['serial_number', 'device_type'], name='unique_serial_per_device_type')
        ]

    def __str__(self):
        device_type_label = self.get_device_type_display()
        if self.name:
            return f"{device_type_label}: {self.serial_number} - {self.name}"
        return f"{device_type_label}: {self.serial_number}"

    @property
    def open_tickets_count(self):
        return self.tickets.filter(status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS]).count()

    @property
    def needs_attention(self):
        if self.status != DeviceStatus.OPERATIONAL:
            return True
        if self.condition != DeviceCondition.GOOD:
            return True
        if self.last_inspected and self.last_inspected <= timezone.now().date() - timezone.timedelta(days=180):
            return True
        if self.tickets.filter(status__in=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS]).exists():
            return True
        return False

class Material(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=50, help_text="e.g., Bundle, Box, Bottle")
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=5, help_text="Alert level for reordering")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.unit}s available)"

    def recommendation(self):
        if self.stock_quantity == 0:
            return f"The store is out of {self.name}. Reorder immediately."
        if self.stock_quantity <= self.min_stock_level:
            return f"Low stock alert for {self.name}. Current stock: {self.stock_quantity} {self.unit}(s)."
        return f"Stock level for {self.name} is healthy."


class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STAFF,
        help_text='Role used for role-based access control.',
    )
    technician_type = models.CharField(
        max_length=50,
        choices=TechnicianType.choices,
        blank=True,
        null=True,
        help_text='Specialization area for technician users.'
    )

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_technician(self):
        return self.role == UserRole.TECHNICIAN

    @property
    def is_property_manager(self):
        return self.role == UserRole.PROPERTY_MANAGER

class MaterialRequest(models.Model):
    requester = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='material_requests'
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name='requests'
    )
    quantity = models.PositiveIntegerField(default=1)
    reason = models.TextField(help_text="Purpose of the request")
    status = models.CharField(
        max_length=20,
        choices=MaterialRequestStatus.choices,
        default=MaterialRequestStatus.PENDING
    )
    approver = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_material_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request for {self.quantity} {self.material.name} by {self.requester.username}"


class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    reported_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name='reported_tickets',
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        null=True,
        blank=True,
    )
    device = models.ForeignKey(
        'Device',
        on_delete=models.SET_NULL,
        related_name='tickets',
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
    )
    priority = models.CharField(
        max_length=20,
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM,
    )
    category = models.CharField(max_length=100, blank=True)
    ai_suggested_category = models.CharField(max_length=100, blank=True, null=True, help_text="AI-suggested category based on description.")
    wing = models.CharField(
        max_length=20,
        choices=WingChoices.choices,
        default=WingChoices.EACJ,
        blank=True,
    )
    floor = models.CharField(
        max_length=20,
        choices=FloorChoices.choices,
        blank=True,
    )
    room_number = models.CharField(max_length=50, blank=True)
    device_serial_number = models.CharField(max_length=150, blank=True, verbose_name='Device serial number')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_at = models.DateTimeField(null=True, blank=True, help_text="SLA Deadline based on priority.")
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    reopened_at = models.DateTimeField(null=True, blank=True)
    reopen_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ticket'
        verbose_name_plural = 'tickets'

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"

    @property
    def is_stale(self):
        if self.status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS):
            return self.updated_at <= timezone.now() - timedelta(days=3)
        return False

    @property
    def is_overdue(self):
        if self.status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS) and self.due_at:
            return timezone.now() > self.due_at
        return False

    @property
    def resolution_duration(self):
        if self.resolved_at and self.created_at:
            return self.resolved_at - self.created_at
        return None

    def set_sla_deadline(self):
        """Calculates the due_at timestamp based on priority."""
        if not self.created_at:
            reference_time = timezone.now()
        else:
            reference_time = self.created_at

        sla_hours = {
            TicketPriority.CRITICAL: 4,
            TicketPriority.HIGH: 24,
            TicketPriority.MEDIUM: 72,
            TicketPriority.LOW: 120,
        }
        self.due_at = reference_time + timedelta(hours=sla_hours.get(self.priority, 72))

    def save(self, *args, **kwargs):
        if self.status == TicketStatus.RESOLVED:
            if self.resolved_at is None:
                self.resolved_at = timezone.now()
        else:
            self.resolved_at = None

        if self.status == TicketStatus.CLOSED:
            if self.closed_at is None:
                self.closed_at = timezone.now()
        else:
            self.closed_at = None

        # Recalculate SLA if due_at is missing OR if priority has changed on an active ticket
        update_sla = False
        if not self.due_at:
            update_sla = True
        elif self.pk:
            old_instance = Ticket.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.priority != self.priority:
                update_sla = True

        if update_sla and self.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]:
            self.set_sla_deadline()

        if self.device:
            self.device_serial_number = self.device.serial_number

        super().save(*args, **kwargs)


class TicketComment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket_comments',
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'ticket comment'
        verbose_name_plural = 'ticket comments'

    def __str__(self):
        return f"Comment by {self.user.get_full_name() if self.user else 'System'} on {self.ticket.title}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    uploaded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket_attachments',
    )
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    description = models.CharField(max_length=250, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ticket attachment'
        verbose_name_plural = 'ticket attachments'

    def __str__(self):
        return f"Attachment for {self.ticket.title} by {self.uploaded_by.get_full_name() if self.uploaded_by else 'System'}"


class AuditLog(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    material_request = models.ForeignKey(
        MaterialRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action_time = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-action_time']
        verbose_name = 'audit log'
        verbose_name_plural = 'audit logs'
        indexes = [
            models.Index(fields=['action_time']),
            models.Index(fields=['action_type']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.action_time:%Y-%m-%d %H:%M:%S} - {self.action_type}"


class KnowledgeBaseArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Detailed steps or information for the staff/technicians.")
    category = models.CharField(max_length=100, blank=True, help_text="e.g., Connectivity, Printing, Software")
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kb_articles'
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Knowledge Base Article'

    def __str__(self):
        return self.title
