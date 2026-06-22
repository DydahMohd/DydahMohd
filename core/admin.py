from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import AuditLog, CustomUser, Ticket, TicketAttachment, TicketComment, Device, KnowledgeBaseArticle, Material, MaterialRequest


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('role', 'technician_type')
    list_filter = UserAdmin.list_filter + ('role', 'technician_type')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role', 'technician_type')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role', 'technician_type')}),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'technician_type' in form.base_fields:
             form.base_fields['technician_type'].required = False
        return form


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'name', 'device_type', 'status', 'condition', 'open_tickets_count_display', 'wing')
    list_filter = ('device_type', 'status', 'condition', 'wing', 'floor')
    search_fields = ('serial_number', 'name', 'notes')

    @admin.display(description='Open Tickets')
    def open_tickets_count_display(self, obj):
        return obj.open_tickets_count

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_quantity', 'unit', 'min_stock_level')
    search_fields = ('name',)

@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ('material', 'quantity', 'requester', 'status', 'created_at')
    list_filter = ('status', 'material')


@admin.register(KnowledgeBaseArticle)
class KnowledgeBaseArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_published', 'created_at')
    list_filter = ('category', 'is_published', 'author')
    search_fields = ('title', 'content', 'category')


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ('user', 'created_at')
    can_delete = False

class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    readonly_fields = ('uploaded_by', 'uploaded_at')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status_tag', 'priority', 'sla_status', 'reported_by', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category', 'assigned_to')
    search_fields = (
        'title', 'description', 
        'reported_by__username', 'reported_by__first_name', 'reported_by__last_name',
        'assigned_to__username', 'assigned_to__first_name', 'assigned_to__last_name'
    )
    readonly_fields = ('created_at', 'updated_at', 'resolved_at', 'closed_at', 'due_at')
    inlines = [TicketCommentInline, TicketAttachmentInline]
    actions = ['mark_as_resolved', 'mark_as_closed']

    @admin.display(description='Status')
    def status_tag(self, obj):
        colors = {
            'open': '#dc3545',        # Red
            'in_progress': '#0d6efd', # Blue
            'resolved': '#198754',    # Green
            'closed': '#6c757d',      # Grey
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )

    @admin.display(description='SLA Status')
    def sla_status(self, obj):
        if obj.status in ['resolved', 'closed']:
            return "Completed"
        if not obj.due_at:
            return "-"
        
        diff = obj.due_at - timezone.now()
        if diff.total_seconds() < 0:
            return format_html('<b style="color: #dc3545;">Overdue</b>')
        
        hours = diff.total_seconds() / 3600
        if hours < 4:
            return format_html('<b style="color: #fd7e14;">{:.1f}h left</b>', hours)
        if hours < 24:
            return format_html('<span style="color: #ffc107;">{:.1f}h left</span>', hours)
        return f"{hours/24:.1f} days"

    @admin.action(description="Mark selected tickets as Resolved")
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_at=timezone.now())

    @admin.action(description="Mark selected tickets as Closed")
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed', closed_at=timezone.now())


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'action_type', 'user', 'ticket', 'ip_address')
    list_filter = ('action_type', 'user')
    search_fields = ('description', 'user__username', 'ticket__title')
    readonly_fields = ('action_time', 'user', 'ticket', 'material_request', 'action_type', 'description', 'ip_address', 'user_agent', 'metadata')

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'uploaded_by', 'uploaded_at')
    search_fields = ('ticket__title', 'uploaded_by__username', 'description')
    readonly_fields = ('uploaded_at',)


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'created_at')
    search_fields = ('ticket__title', 'user__username', 'comment')
    readonly_fields = ('created_at',)
