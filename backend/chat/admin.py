from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ChatSession, Message, ToolExecution, SessionSnapshot, ChatAnalytics


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'get_display_name', 'status', 'model_name', 'message_count', 'created_at', 'last_activity']
    list_filter = ['status', 'model_name', 'provider', 'approval_mode', 'created_at']
    search_fields = ['session_name', 'user__email', 'user__username']
    readonly_fields = ['session_id', 'created_at', 'updated_at', 'message_count', 'total_tokens_used']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('session_id', 'user', 'session_name', 'status')
        }),
        ('AI Configuration', {
            'fields': ('model_name', 'provider', 'approval_mode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('message_count', 'total_tokens_used')
        }),
        ('Advanced Settings', {
            'fields': ('settings',),
            'classes': ('collapse',)
        })
    )
    
    def get_display_name(self, obj):
        return obj.get_display_name()
    get_display_name.short_description = 'Display Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'session_link', 'role', 'content_preview', 'sequence_number', 'timestamp', 'tokens_used']
    list_filter = ['role', 'timestamp', 'session__status']
    search_fields = ['content', 'session__session_name', 'session__user__email']
    readonly_fields = ['message_id', 'timestamp', 'sequence_number']
    raw_id_fields = ['session']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('message_id', 'session', 'role', 'sequence_number')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Metadata', {
            'fields': ('timestamp', 'tokens_used', 'processing_time', 'model_used'),
            'classes': ('collapse',)
        }),
        ('Tool Data', {
            'fields': ('tools_used', 'tool_results'),
            'classes': ('collapse',)
        }),
        ('Additional Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def session_link(self, obj):
        url = reverse('admin:chat_chatsession_change', args=[obj.session.session_id])
        return format_html('<a href="{}">{}</a>', url, str(obj.session.session_id)[:8])
    session_link.short_description = 'Session'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__user')


@admin.register(ToolExecution)
class ToolExecutionAdmin(admin.ModelAdmin):
    list_display = ['execution_id', 'session_link', 'tool_name', 'status', 'started_at', 'execution_time', 'requires_approval']
    list_filter = ['status', 'tool_name', 'requires_approval', 'started_at']
    search_fields = ['tool_name', 'tool_description', 'session__session_name', 'session__user__email']
    readonly_fields = ['execution_id', 'started_at', 'completed_at', 'execution_time']
    raw_id_fields = ['session', 'message', 'approved_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('execution_id', 'session', 'message', 'tool_name', 'tool_description', 'tool_source')
        }),
        ('Execution Details', {
            'fields': ('arguments', 'result', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'execution_time'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Approval Workflow', {
            'fields': ('requires_approval', 'approved_by', 'approved_at', 'approval_notes'),
            'classes': ('collapse',)
        })
    )
    
    def session_link(self, obj):
        url = reverse('admin:chat_chatsession_change', args=[obj.session.session_id])
        return format_html('<a href="{}">{}</a>', url, str(obj.session.session_id)[:8])
    session_link.short_description = 'Session'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__user', 'approved_by')


@admin.register(SessionSnapshot)
class SessionSnapshotAdmin(admin.ModelAdmin):
    list_display = ['snapshot_id', 'session_link', 'created_by', 'description', 'message_count_at_snapshot', 'created_at']
    list_filter = ['created_at']
    search_fields = ['description', 'session__session_name', 'created_by__email']
    readonly_fields = ['snapshot_id', 'created_at', 'message_count_at_snapshot', 'tokens_used_at_snapshot']
    raw_id_fields = ['session', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('snapshot_id', 'session', 'created_by', 'description', 'created_at')
        }),
        ('Snapshot Statistics', {
            'fields': ('message_count_at_snapshot', 'tokens_used_at_snapshot')
        }),
        ('Snapshot Data', {
            'fields': ('session_data', 'messages_data', 'tools_data'),
            'classes': ('collapse',)
        })
    )
    
    def session_link(self, obj):
        url = reverse('admin:chat_chatsession_change', args=[obj.session.session_id])
        return format_html('<a href="{}">{}</a>', url, str(obj.session.session_id)[:8])
    session_link.short_description = 'Session'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'session__user', 'created_by')


@admin.register(ChatAnalytics)
class ChatAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'sessions_created', 'messages_sent', 'messages_received', 'total_tokens_used', 'tools_executed']
    list_filter = ['date']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['analytics_id']
    raw_id_fields = ['user']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('analytics_id', 'user', 'date')
        }),
        ('Usage Statistics', {
            'fields': ('sessions_created', 'messages_sent', 'messages_received', 'total_tokens_used', 'tools_executed')
        }),
        ('Session Duration', {
            'fields': ('total_session_time', 'avg_session_time'),
            'classes': ('collapse',)
        }),
        ('Detailed Breakdown', {
            'fields': ('model_usage', 'tool_usage'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Custom admin actions
def mark_sessions_inactive(modeladmin, request, queryset):
    queryset.update(status='inactive')
mark_sessions_inactive.short_description = "Mark selected sessions as inactive"

def archive_sessions(modeladmin, request, queryset):
    queryset.update(status='archived')
archive_sessions.short_description = "Archive selected sessions"

# Add actions to ChatSessionAdmin
ChatSessionAdmin.actions = [mark_sessions_inactive, archive_sessions]
