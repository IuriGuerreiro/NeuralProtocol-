from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatSession, Message, ToolExecution, SessionSnapshot, ChatAnalytics

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'role', 'content', 'timestamp', 'sequence_number',
            'tokens_used', 'processing_time', 'model_used', 'tools_used', 
            'tool_results', 'metadata'
        ]
        read_only_fields = ['message_id', 'timestamp', 'sequence_number']


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing chat sessions"""
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'session_id', 'display_name', 'session_name', 'status', 
            'model_name', 'provider', 'message_count', 'created_at', 
            'last_activity'
        ]
        read_only_fields = ['session_id', 'display_name', 'message_count', 'created_at', 'last_activity']


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for chat sessions"""
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'session_id', 'display_name', 'session_name', 'status', 
            'model_name', 'provider', 'approval_mode', 'settings',
            'message_count', 'total_tokens_used', 'created_at', 
            'updated_at', 'last_activity', 'user_email'
        ]
        read_only_fields = [
            'session_id', 'display_name', 'message_count', 'total_tokens_used', 
            'created_at', 'updated_at', 'last_activity', 'user_email'
        ]


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat sessions"""
    
    class Meta:
        model = ChatSession
        fields = ['session_name', 'model_name', 'provider', 'approval_mode', 'settings']
        
    def create(self, validated_data):
        # Add the user from the request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ToolExecutionSerializer(serializers.ModelSerializer):
    """Serializer for tool executions"""
    session_id = serializers.UUIDField(source='session.session_id', read_only=True)
    message_id = serializers.UUIDField(source='message.message_id', read_only=True)
    
    class Meta:
        model = ToolExecution
        fields = [
            'execution_id', 'session_id', 'message_id', 'tool_name', 
            'tool_description', 'tool_source', 'arguments', 'result',
            'status', 'started_at', 'completed_at', 'execution_time',
            'error_message', 'retry_count', 'requires_approval',
            'approved_at', 'approval_notes'
        ]
        read_only_fields = [
            'execution_id', 'session_id', 'message_id', 'started_at', 
            'completed_at', 'execution_time', 'approved_at'
        ]


class SessionSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for session snapshots"""
    session_id = serializers.UUIDField(source='session.session_id', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = SessionSnapshot
        fields = [
            'snapshot_id', 'session_id', 'created_by_email', 'description',
            'created_at', 'message_count_at_snapshot', 'tokens_used_at_snapshot',
            'session_data', 'messages_data', 'tools_data'
        ]
        read_only_fields = [
            'snapshot_id', 'session_id', 'created_by_email', 'created_at',
            'message_count_at_snapshot', 'tokens_used_at_snapshot'
        ]
        
    def create(self, validated_data):
        # Add the user and session from the request context
        validated_data['created_by'] = self.context['request'].user
        validated_data['session_id'] = self.context['session_id']
        return super().create(validated_data)


class ChatAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for chat analytics"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ChatAnalytics
        fields = [
            'analytics_id', 'user_email', 'date', 'sessions_created',
            'messages_sent', 'messages_received', 'total_tokens_used',
            'tools_executed', 'total_session_time', 'avg_session_time',
            'model_usage', 'tool_usage'
        ]
        read_only_fields = ['analytics_id', 'user_email']


# API Response Serializers (matching the FastAPI models)
class MessageResponseSerializer(serializers.Serializer):
    """Serializer for API message response format"""
    id = serializers.UUIDField(source='message_id')
    role = serializers.CharField()
    content = serializers.CharField()
    timestamp = serializers.DateTimeField()
    session_id = serializers.UUIDField(source='session.session_id')


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for API chat response format"""
    user_message = MessageResponseSerializer()
    assistant_message = MessageResponseSerializer()
    session_id = serializers.UUIDField()


class ChatHistoryResponseSerializer(serializers.Serializer):
    """Serializer for API chat history response format"""
    session_id = serializers.UUIDField()
    messages = MessageResponseSerializer(many=True)
    total_messages = serializers.IntegerField()


class SystemStatusResponseSerializer(serializers.Serializer):
    """Serializer for API system status response format"""
    session_id = serializers.UUIDField()
    llm_status = serializers.CharField()
    agent_status = serializers.CharField()
    stdio_servers = serializers.ListField(child=serializers.CharField())
    http_servers = serializers.ListField(child=serializers.CharField())
    tools_summary = serializers.DictField()
    message_count = serializers.IntegerField()
    approval_mode = serializers.BooleanField()


class ToolsSummaryResponseSerializer(serializers.Serializer):
    """Serializer for API tools summary response format"""
    total_tools = serializers.IntegerField()
    mcp_tools = serializers.DictField()
    http_tools = serializers.DictField()
    custom_tools = serializers.DictField()
    servers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )