from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import json

User = get_user_model()


class ChatSession(models.Model):
    """
    Chat session model - represents a conversation session between user and AI
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('archived', 'Archived'),
    ]
    
    # Primary fields
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_name = models.CharField(max_length=255, blank=True, null=True)
    
    # AI Configuration
    model_name = models.CharField(max_length=100, default='gemini-2.0-flash')
    provider = models.CharField(max_length=50, default='google_genai')
    
    # Session state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Configuration and settings
    approval_mode = models.BooleanField(default=False, help_text="Whether tool approval is required")
    settings = models.JSONField(default=dict, blank=True, help_text="Session-specific settings")
    
    # Statistics
    message_count = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        name = self.session_name or f"Chat {str(self.session_id)[:8]}"
        return f"{name} ({self.user.email})"
    
    def get_display_name(self):
        """Get a user-friendly display name for the session"""
        if self.session_name:
            return self.session_name
        return f"Chat {str(self.session_id)[:8]}..."
    
    def increment_message_count(self, count=1):
        """Increment the message count"""
        self.message_count = models.F('message_count') + count
        self.save(update_fields=['message_count', 'last_activity'])
        # Refresh from database to get the actual value
        self.refresh_from_db(fields=['message_count'])
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class Message(models.Model):
    """
    Chat message model - represents individual messages in a conversation
    """
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
        ('tool', 'Tool'),
    ]
    
    # Primary fields
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    # Message content
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    sequence_number = models.PositiveIntegerField(help_text="Order of message in conversation")
    
    # AI response metadata (for assistant messages)
    tokens_used = models.PositiveIntegerField(default=0, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Time in seconds to generate response")
    model_used = models.CharField(max_length=100, blank=True, null=True)
    
    # Tool usage (if applicable)
    tools_used = models.JSONField(default=list, blank=True, help_text="List of tools used in this message")
    tool_results = models.JSONField(default=dict, blank=True, help_text="Results from tool executions")
    
    # Message metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional message metadata")
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['sequence_number']
        indexes = [
            models.Index(fields=['session', 'sequence_number']),
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['role', 'timestamp']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['session', 'sequence_number'], name='unique_sequence_per_session')
        ]
    
    def __str__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.role}: {content_preview} (Session: {str(self.session.session_id)[:8]})"
    
    def save(self, *args, **kwargs):
        # Auto-increment sequence number if not set
        if self.sequence_number is None:
            last_message = Message.objects.filter(session=self.session).order_by('-sequence_number').first()
            self.sequence_number = (last_message.sequence_number + 1) if last_message else 1
        
        super().save(*args, **kwargs)
    
    @property
    def is_user_message(self):
        return self.role == 'user'
    
    @property
    def is_assistant_message(self):
        return self.role == 'assistant'
    
    @property
    def is_system_message(self):
        return self.role == 'system'


class ToolExecution(models.Model):
    """
    Tool execution tracking - detailed logging of tool usage
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    # Primary fields
    execution_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='tool_executions')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='tool_executions', null=True, blank=True)
    
    # Tool information
    tool_name = models.CharField(max_length=100)
    tool_description = models.TextField(blank=True)
    tool_source = models.CharField(max_length=100, blank=True, help_text="MCP server or custom tool source")
    
    # Execution details
    arguments = models.JSONField(default=dict, help_text="Arguments passed to the tool")
    result = models.JSONField(default=dict, blank=True, help_text="Result returned by the tool")
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True, help_text="Execution time in seconds")
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_tools')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'chat_tool_executions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['session', '-started_at']),
            models.Index(fields=['tool_name', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"Tool: {self.tool_name} ({self.status}) - Session: {str(self.session.session_id)[:8]}"
    
    def mark_completed(self, result=None):
        """Mark the tool execution as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if result is not None:
            self.result = result
        if self.started_at and self.completed_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
        self.save()
    
    def mark_failed(self, error_message=""):
        """Mark the tool execution as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        if self.started_at and self.completed_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
        self.save()


class SessionSnapshot(models.Model):
    """
    Session snapshots for backup and restoration
    """
    
    snapshot_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='snapshots')
    
    # Snapshot metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    
    # Snapshot data
    session_data = models.JSONField(help_text="Serialized session state")
    messages_data = models.JSONField(help_text="Serialized messages")
    tools_data = models.JSONField(default=list, help_text="Serialized tool executions")
    
    # Statistics at time of snapshot
    message_count_at_snapshot = models.PositiveIntegerField(default=0)
    tokens_used_at_snapshot = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'chat_session_snapshots'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', '-created_at']),
        ]
    
    def __str__(self):
        return f"Snapshot of {self.session} at {self.created_at}"


class ChatAnalytics(models.Model):
    """
    Analytics and usage tracking for chat sessions
    """
    
    analytics_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_analytics')
    
    # Time period
    date = models.DateField()
    
    # Usage statistics
    sessions_created = models.PositiveIntegerField(default=0)
    messages_sent = models.PositiveIntegerField(default=0)
    messages_received = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    tools_executed = models.PositiveIntegerField(default=0)
    
    # Session duration statistics (in seconds)
    total_session_time = models.PositiveIntegerField(default=0)
    avg_session_time = models.FloatField(default=0.0)
    
    # Model usage breakdown
    model_usage = models.JSONField(default=dict, help_text="Usage breakdown by AI model")
    tool_usage = models.JSONField(default=dict, help_text="Usage breakdown by tools")
    
    class Meta:
        db_table = 'chat_analytics'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['date']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_analytics_per_day')
        ]
    
    def __str__(self):
        return f"Analytics for {self.user.email} on {self.date}"