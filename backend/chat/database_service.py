"""
Database Service for Chat System

Service layer for managing chat data persistence and retrieval.
Handles all database operations for the chat system using Django ORM.
"""

from typing import List, Optional, Dict, Any
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, timedelta
import json

from .models import ChatSession, Message, ToolExecution, SessionSnapshot, ChatAnalytics

User = get_user_model()


class ChatDatabaseService:
    """Service class for chat database operations"""
    
    # Session Management
    def create_session(
        self, 
        user: User, 
        session_name: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        provider: str = "google_genai",
        approval_mode: bool = False,
        settings: Optional[Dict] = None
    ) -> ChatSession:
        """Create a new chat session"""
        return ChatSession.objects.create(
            user=user,
            session_name=session_name,
            model_name=model_name,
            provider=provider,
            approval_mode=approval_mode,
            settings=settings or {}
        )
    
    def get_session(self, session_id: str, user: User) -> Optional[ChatSession]:
        """Get a chat session by ID for a specific user"""
        try:
            return ChatSession.objects.select_related('user').get(
                session_id=session_id, 
                user=user
            )
        except ChatSession.DoesNotExist:
            return None
    
    def get_user_sessions(
        self, 
        user: User, 
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ChatSession]:
        """Get all sessions for a user"""
        queryset = ChatSession.objects.filter(user=user)
        
        if status:
            queryset = queryset.filter(status=status)
            
        queryset = queryset.order_by('-last_activity')
        
        if limit:
            queryset = queryset[:limit]
            
        return list(queryset)
    
    def update_session(
        self, 
        session_id: str, 
        user: User, 
        **kwargs
    ) -> Optional[ChatSession]:
        """Update a chat session"""
        try:
            session = ChatSession.objects.get(session_id=session_id, user=user)
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.save()
            return session
        except ChatSession.DoesNotExist:
            return None
    
    def delete_session(self, session_id: str, user: User) -> bool:
        """Delete a chat session"""
        try:
            ChatSession.objects.get(session_id=session_id, user=user).delete()
            return True
        except ChatSession.DoesNotExist:
            return False
    
    def update_session_activity(self, session: ChatSession) -> None:
        """Update the last activity timestamp for a session"""
        session.update_activity()
    
    # Message Management
    def save_message(
        self,
        session: ChatSession,
        role: str,
        content: str,
        tokens_used: int = 0,
        processing_time: Optional[float] = None,
        model_used: Optional[str] = None,
        tools_used: Optional[List] = None,
        tool_results: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> Message:
        """Save a message to the database"""
        with transaction.atomic():
            message = Message.objects.create(
                session=session,
                role=role,
                content=content,
                tokens_used=tokens_used,
                processing_time=processing_time,
                model_used=model_used,
                tools_used=tools_used or [],
                tool_results=tool_results or {},
                metadata=metadata or {}
            )
            
            # Update session statistics
            session.increment_message_count()
            if tokens_used > 0:
                session.total_tokens_used += tokens_used
                session.save(update_fields=['total_tokens_used'])
            
            return message
    
    def get_session_messages(
        self, 
        session: ChatSession, 
        limit: Optional[int] = None,
        offset: int = 0,
        role_filter: Optional[str] = None
    ) -> List[Message]:
        """Get messages for a session"""
        queryset = Message.objects.filter(session=session)
        
        if role_filter:
            queryset = queryset.filter(role=role_filter)
            
        queryset = queryset.order_by('sequence_number')
        
        if offset > 0:
            queryset = queryset[offset:]
            
        if limit:
            queryset = queryset[:limit]
            
        return list(queryset)
    
    def get_recent_messages_for_context(
        self,
        session: ChatSession,
        limit: int = 10,
        exclude_system: bool = True
    ) -> List[Dict[str, str]]:
        """Get recent messages formatted for LLM context.
        
        Args:
            session: Chat session to get messages from
            limit: Number of recent messages to retrieve
            exclude_system: Whether to exclude system messages
            
        Returns:
            List of message dicts with role and content
        """
        queryset = Message.objects.filter(session=session)
        
        if exclude_system:
            queryset = queryset.exclude(role='system')
            
        # Get most recent messages, ordered by sequence_number descending
        recent_messages = queryset.order_by('-sequence_number')[:limit]
        
        # Convert to list and reverse to get chronological order
        messages_list = list(recent_messages)
        messages_list.reverse()
        
        # Format for LLM context
        context_messages = []
        for msg in messages_list:
            context_messages.append({
                'role': msg.role,
                'content': msg.content
            })
            
        return context_messages
    
    def get_message_count(self, session: ChatSession, role_filter: Optional[str] = None) -> int:
        """Get total message count for a session"""
        queryset = Message.objects.filter(session=session)
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        return queryset.count()
    
    def clear_session_messages(self, session: ChatSession) -> int:
        """Clear all messages for a session (except system messages)"""
        with transaction.atomic():
            deleted_count = Message.objects.filter(
                session=session
            ).exclude(role='system').delete()[0]
            
            # Update session statistics
            session.message_count = Message.objects.filter(session=session).count()
            session.save(update_fields=['message_count', 'last_activity'])
            
            return deleted_count
    
    # Tool Execution Management
    def create_tool_execution(
        self,
        session: ChatSession,
        tool_name: str,
        tool_description: str = "",
        tool_source: str = "",
        arguments: Dict = None,
        requires_approval: bool = False,
        message: Optional[Message] = None
    ) -> ToolExecution:
        """Create a new tool execution record"""
        return ToolExecution.objects.create(
            session=session,
            message=message,
            tool_name=tool_name,
            tool_description=tool_description,
            tool_source=tool_source,
            arguments=arguments or {},
            requires_approval=requires_approval
        )
    
    def update_tool_execution(
        self,
        execution_id: str,
        **kwargs
    ) -> Optional[ToolExecution]:
        """Update a tool execution"""
        try:
            execution = ToolExecution.objects.get(execution_id=execution_id)
            for key, value in kwargs.items():
                if hasattr(execution, key):
                    setattr(execution, key, value)
            execution.save()
            return execution
        except ToolExecution.DoesNotExist:
            return None
    
    def get_session_tool_executions(
        self,
        session: ChatSession,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ToolExecution]:
        """Get tool executions for a session"""
        queryset = ToolExecution.objects.filter(session=session)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        queryset = queryset.order_by('-started_at')
        
        if limit:
            queryset = queryset[:limit]
            
        return list(queryset)
    
    # Session Snapshots
    def create_session_snapshot(
        self,
        session: ChatSession,
        created_by: User,
        description: str = ""
    ) -> SessionSnapshot:
        """Create a session snapshot"""
        # Get current session data
        messages = self.get_session_messages(session)
        tools = self.get_session_tool_executions(session)
        
        # Serialize data
        session_data = {
            'session_name': session.session_name,
            'model_name': session.model_name,
            'provider': session.provider,
            'approval_mode': session.approval_mode,
            'settings': session.settings,
            'status': session.status
        }
        
        messages_data = [
            {
                'role': msg.role,
                'content': msg.content,
                'sequence_number': msg.sequence_number,
                'timestamp': msg.timestamp.isoformat(),
                'tokens_used': msg.tokens_used,
                'tools_used': msg.tools_used,
                'tool_results': msg.tool_results
            }
            for msg in messages
        ]
        
        tools_data = [
            {
                'tool_name': tool.tool_name,
                'arguments': tool.arguments,
                'result': tool.result,
                'status': tool.status,
                'started_at': tool.started_at.isoformat()
            }
            for tool in tools
        ]
        
        return SessionSnapshot.objects.create(
            session=session,
            created_by=created_by,
            description=description,
            session_data=session_data,
            messages_data=messages_data,
            tools_data=tools_data,
            message_count_at_snapshot=len(messages),
            tokens_used_at_snapshot=session.total_tokens_used
        )
    
    def get_session_snapshots(
        self,
        session: ChatSession,
        limit: Optional[int] = None
    ) -> List[SessionSnapshot]:
        """Get snapshots for a session"""
        queryset = SessionSnapshot.objects.filter(session=session).order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
            
        return list(queryset)
    
    # Analytics
    def update_daily_analytics(self, user: User, **kwargs) -> ChatAnalytics:
        """Update or create daily analytics for a user"""
        today = timezone.now().date()
        
        # Include date in defaults to ensure it's set correctly
        defaults = kwargs.copy()
        defaults['date'] = today
        
        analytics, created = ChatAnalytics.objects.get_or_create(
            user=user,
            date=today,
            defaults=defaults
        )
        
        if not created:
            # Update existing analytics
            for key, value in kwargs.items():
                if hasattr(analytics, key):
                    current_value = getattr(analytics, key)
                    if isinstance(current_value, (int, float)):
                        setattr(analytics, key, current_value + value)
                    elif isinstance(current_value, dict):
                        # Merge dictionaries
                        merged = current_value.copy()
                        merged.update(value)
                        setattr(analytics, key, merged)
            analytics.save()
        
        return analytics
    
    def get_user_analytics(
        self,
        user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ChatAnalytics]:
        """Get analytics for a user within date range"""
        queryset = ChatAnalytics.objects.filter(user=user)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date.date())
        if end_date:
            queryset = queryset.filter(date__lte=end_date.date())
            
        return list(queryset.order_by('-date'))
    
    # Utility Methods
    def get_session_statistics(self, session: ChatSession) -> Dict[str, Any]:
        """Get comprehensive statistics for a session"""
        messages = Message.objects.filter(session=session)
        tools = ToolExecution.objects.filter(session=session)
        
        return {
            'total_messages': messages.count(),
            'user_messages': messages.filter(role='user').count(),
            'assistant_messages': messages.filter(role='assistant').count(),
            'system_messages': messages.filter(role='system').count(),
            'total_tokens': session.total_tokens_used,
            'avg_tokens_per_message': messages.aggregate(
                avg=Avg('tokens_used')
            )['avg'] or 0,
            'total_tools_executed': tools.count(),
            'successful_tools': tools.filter(status='completed').count(),
            'failed_tools': tools.filter(status='failed').count(),
            'pending_tools': tools.filter(status='pending').count(),
            'session_duration': (
                timezone.now() - session.created_at
            ).total_seconds() if session.status == 'active' else None,
            'last_activity': session.last_activity,
            'approval_mode': session.approval_mode
        }
    
    def search_messages(
        self,
        user: User,
        query: str,
        session_id: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 50
    ) -> List[Message]:
        """Search messages by content"""
        queryset = Message.objects.filter(session__user=user)
        
        if session_id:
            queryset = queryset.filter(session__session_id=session_id)
        if role:
            queryset = queryset.filter(role=role)
            
        # Full text search
        queryset = queryset.filter(content__icontains=query)
        
        return list(queryset.select_related('session').order_by('-timestamp')[:limit])
    
    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Archive or delete old inactive sessions"""
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        with transaction.atomic():
            # Mark old sessions as archived
            updated_count = ChatSession.objects.filter(
                last_activity__lt=cutoff_date,
                status='active'
            ).update(status='archived')
            
            return updated_count


# Create singleton instance
chat_db = ChatDatabaseService()