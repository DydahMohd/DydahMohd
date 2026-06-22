import io
from datetime import timedelta
from django.db.models import Avg, Count, F
from django.utils import timezone
from .models import Ticket, TicketStatus, TicketPriority

def get_executive_summary_stats(queryset):
    """
    Computes statistics for the executive summary section of the audit report.
    """
    total_count = queryset.count()
    if total_count == 0:
        return {
            'total_count': 0,
            'resolved_count': 0,
            'avg_resolution_time': "N/A",
            'most_common_category': "N/A",
            'completion_rate': 0
        }

    resolved_tickets = queryset.filter(status=TicketStatus.RESOLVED, resolved_at__isnull=False)
    resolved_count = resolved_tickets.count()
    
    # Calculate average resolution time
    avg_res_time = "N/A"
    if resolved_count > 0:
        durations = resolved_tickets.annotate(
            duration=F('resolved_at') - F('created_at')
        ).aggregate(avg_duration=Avg('duration'))
        
        avg_duration = durations['avg_duration']
        if avg_duration:
            days = avg_duration.days
            hours = avg_duration.seconds // 3600
            avg_res_time = f"{days}d {hours}h"

    # Determine most common category
    category_counts = queryset.values('category').annotate(count=Count('id')).order_by('-count')
    most_common_category = category_counts[0]['category'] if category_counts and category_counts[0]['category'] else "Uncategorized"

    return {
        'total_count': total_count,
        'resolved_count': resolved_count,
        'avg_resolution_time': avg_res_time,
        'most_common_category': most_common_category,
        'completion_rate': round((resolved_count / total_count) * 100, 1)
    }

def generate_recommendations(stats):
    """
    Auto-generates text-based recommendations based on computed stats.
    """
    recommendations = []
    
    if stats['completion_rate'] < 75:
        recommendations.append("The ticket resolution rate is below 75%. Consider reviewing technician workloads.")
    
    if stats['total_count'] > 0:
        recommendations.append(f"The most frequent issue category is '{stats['most_common_category']}'. Target this area for proactive maintenance.")
    
    if not recommendations:
        recommendations.append("Performance metrics are within healthy ranges. No immediate action required.")
        
    return recommendations

def get_audit_trail_for_report(ticket_ids):
    """
    Fetches relevant audit logs for the list of tickets provided in a report.
    """
    from .models import AuditLog
    return AuditLog.objects.filter(ticket_id__in=ticket_ids).order_by('ticket_id', '-action_time')