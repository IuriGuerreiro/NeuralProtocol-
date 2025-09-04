"""
Django-style Chat API Views

Django REST Framework views for the chat system with proper database persistence.
Replaces the FastAPI endpoints with Django-style class-based views.
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from asgiref.sync import sync_to_async, async_to_sync
from typing import Optional
import time
import asyncio
import uuid
import threading
import concurrent.futures
import multiprocessing
import logging
import subprocess
import json
import os
import sys

from .models import ChatSession, Message, ToolExecution, SessionSnapshot
from .serializers import (
    ChatSessionListSerializer, ChatSessionDetailSerializer, ChatSessionCreateSerializer,
    MessageSerializer, MessageResponseSerializer, ChatResponseSerializer,
    ChatHistoryResponseSerializer, SystemStatusResponseSerializer,
    ToolExecutionSerializer, SessionSnapshotSerializer
)
from .database_service import chat_db
from .langchain_chat import NeuralProtocolChat
from .global_tools import global_tools_manager

User = get_user_model()


class ChatSessionViewSet(ModelViewSet):
    """ViewSet for managing chat sessions"""
    
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'session_id'
    
    async def _create_fast_chat_instance(self, session):
        """Create a fast chat instance using global tools"""
        chat_instance = NeuralProtocolChat()
        chat_instance.chat_history.session_id = str(session.session_id)
        
        # Initialize LLM only (tools are global)
        await chat_instance.initialize_llm(
            model_name=session.model_name,
            provider=session.provider
        )
        
        # Use global tools instead of initializing new ones
        chat_instance.tools_manager = global_tools_manager.tools_manager
        chat_instance.mcp_studio = global_tools_manager.mcp_studio
        chat_instance.http_mcp_studio = global_tools_manager.http_mcp_studio
        
        # Set approval mode from session settings
        global_tools_manager.set_approval_mode(session.approval_mode)
        
        # Create agent with global tools
        await chat_instance.create_agent()
        
        return chat_instance
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        elif self.action == 'create':
            return ChatSessionCreateSerializer
        else:
            return ChatSessionDetailSerializer
    
    def create(self, request):
        """Create a new chat session"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create session in database
        session = chat_db.create_session(
            user=request.user,
            session_name=serializer.validated_data.get('session_name'),
            model_name=serializer.validated_data.get('model_name', 'gemini-2.0-flash'),
            provider=serializer.validated_data.get('provider', 'google_genai'),
            approval_mode=serializer.validated_data.get('approval_mode', False),
            settings=serializer.validated_data.get('settings', {})
        )
        
        # Add system message to database (no need to store chat instance globally)
        try:
            chat_db.save_message(
                session=session,
                role='system',
                content="You are a helpful AI assistant with access to various tools. Use them to help answer user questions."
            )
        except Exception as e:
            # If system message fails, delete the session and return error
            session.delete()
            return Response(
                {'error': f'Failed to create system message: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Return response using list serializer
        response_serializer = ChatSessionListSerializer(session)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, session_id=None):
        """Delete a chat session"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        # No need for cleanup since we're not persisting instances
        session.delete()
        return Response({'message': f'Chat session {session_id} deleted successfully'})
    
    @action(detail=True, methods=['post'])
    def messages(self, request, session_id=None):
        """Send a message and get AI response"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        content = request.data.get('content')
        if not content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_time = time.time()
            
            # Save user message to database
            user_message = chat_db.save_message(
                session=session,
                role='user',
                content=content
            )
            
            # Process message using global tools (no reinitialization)
            try:
                # Define async function to handle chat processing with global tools
                async def process_with_global_tools():
                    # Create fresh NeuralProtocolChat instance but reuse global tools
                    chat_instance = NeuralProtocolChat()
                    
                    # Initialize only the LLM (use global tools for everything else)
                    await chat_instance.initialize_llm(
                        model_name=session.model_name,
                        provider=session.provider
                    )
                    
                    # Use global tools instead of initializing new ones
                    chat_instance.tools_manager = global_tools_manager.tools_manager
                    chat_instance.mcp_studio = global_tools_manager.mcp_studio  
                    chat_instance.http_mcp_studio = global_tools_manager.http_mcp_studio
                    
                    # Set approval mode from session settings
                    global_tools_manager.set_approval_mode(session.approval_mode)
                    
                    # Create agent with global tools (fast since tools are already loaded)
                    await chat_instance.create_agent()
                    
                    # Process single message without any context
                    response = await chat_instance.process_message(content)
                    return response
                
                # Run the async function in sync context
                assistant_response = async_to_sync(process_with_global_tools)()
                
            except Exception as e:
                return Response(
                    {'error': f'Failed to process message: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            processing_time = time.time() - start_time
            
            # Save assistant response to database
            assistant_message = chat_db.save_message(
                session=session,
                role='assistant',
                content=assistant_response,
                processing_time=processing_time,
                model_used=session.model_name
            )
            
            # Update session activity
            chat_db.update_session_activity(session)
            
            # Update analytics
            chat_db.update_daily_analytics(
                user=request.user,
                messages_sent=1,
                messages_received=1
            )
            
            # Return response in API format
            response_data = {
                'user_message': {
                    'id': str(user_message.message_id),
                    'role': user_message.role,
                    'content': user_message.content,
                    'timestamp': user_message.timestamp,
                    'session_id': str(session.session_id)
                },
                'assistant_message': {
                    'id': str(assistant_message.message_id),
                    'role': assistant_message.role,
                    'content': assistant_message.content,
                    'timestamp': assistant_message.timestamp,
                    'session_id': str(session.session_id)
                },
                'session_id': str(session.session_id)
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to process message: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def history(self, request, session_id=None):
        """Get chat history for a session"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        # Get pagination parameters
        limit = request.query_params.get('limit')
        offset = int(request.query_params.get('offset', 0))
        
        if limit:
            limit = int(limit)
        
        # Get messages from database
        messages = chat_db.get_session_messages(
            session=session,
            limit=limit,
            offset=offset
        )
        
        total_messages = chat_db.get_message_count(session)
        
        # Format response
        message_data = []
        for msg in messages:
            message_data.append({
                'id': str(msg.message_id),
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp,
                'session_id': str(session.session_id)
            })
        
        response_data = {
            'session_id': str(session.session_id),
            'messages': message_data,
            'total_messages': total_messages
        }
        
        return Response(response_data)
    
    @action(detail=True, methods=['delete'])
    def clear_history(self, request, session_id=None):
        """Clear chat history for a session"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        deleted_count = chat_db.clear_session_messages(session)
        
        # Re-add system message
        chat_db.save_message(
            session=session,
            role='system',
            content="You are a helpful AI assistant with access to various tools. Use them to help answer user questions."
        )
        
        return Response({'message': 'Chat history cleared successfully'})
    
    @action(detail=True, methods=['get'])
    def status(self, request, session_id=None):
        """Get system status for a session"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        # Create a fast instance to check status  
        try:
            def run_status_in_thread():
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    return loop.run_until_complete(self._create_fast_chat_instance(session))
                finally:
                    loop.close()
            
            # Run the status check in a separate thread to avoid async context issues
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_status_in_thread)
                chat_instance = future.result(timeout=30)  # 30 second timeout
        except Exception as e:
            return Response(
                {'error': f'Failed to create chat instance: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Get server information
        stdio_servers = [server.name for server in chat_instance.mcp_studio.get_initialized_servers()]
        http_servers = [f"{server.name} ({server.config.transport})" 
                       for server in chat_instance.http_mcp_studio.get_initialized_servers()]
        
        # Get tools summary
        tools_summary = chat_instance.tools_manager.get_tools_summary()
        
        response_data = {
            'session_id': str(session.session_id),
            'llm_status': 'initialized' if chat_instance.llm else 'not_initialized',
            'agent_status': 'ready' if chat_instance.agent else 'not_ready',
            'stdio_servers': stdio_servers,
            'http_servers': http_servers,
            'tools_summary': tools_summary,
            'message_count': session.message_count,
            'approval_mode': chat_instance.tools_manager.approval_enabled
        }
        
        return Response(response_data)
    
    @action(detail=True, methods=['get'])
    def tools(self, request, session_id=None):
        """Get tools summary for a session"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        # Use global tools manager directly for tools info
        try:
            tools_summary = global_tools_manager.get_tools_summary()
            
            # Get server information from global managers
            servers = []
            for server in global_tools_manager.mcp_studio.get_initialized_servers():
                servers.append({"name": server.name, "type": "STDIO"})
            for server in global_tools_manager.http_mcp_studio.get_initialized_servers():
                servers.append({"name": server.name, "type": f"HTTP/{server.config.transport}"})
                
        except Exception as e:
            return Response(
                {'error': f'Failed to get tools info: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
        response_data = {
            'total_tools': tools_summary["total_tools"],
            'mcp_tools': tools_summary["mcp_tools"],
            'http_tools': tools_summary["http_tools"],
            'custom_tools': tools_summary["custom_tools"],
            'servers': servers
        }
        
        return Response(response_data)
    
    @action(detail=True, methods=['put'])
    def approval_mode(self, request, session_id=None):
        """Toggle approval mode for a session"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        # Toggle approval mode in database
        current_status = session.approval_mode
        session.approval_mode = not current_status
        session.save(update_fields=['approval_mode'])
        
        # Update global tools manager (will be applied to new chat instances)
        global_tools_manager.set_approval_mode(not current_status)
        
        return Response({
            'approval_mode': not current_status,
            'message': f"Tool approval mode {'enabled' if not current_status else 'disabled'}"
        })
    
    @action(detail=True, methods=['put'])
    def context_settings(self, request, session_id=None):
        """Update conversation context settings for a session"""
        session = get_object_or_404(self.get_queryset(), session_id=session_id)
        
        # Get the context message limit from request
        context_messages = request.data.get('context_messages')
        
        if context_messages is not None:
            try:
                context_messages = int(context_messages)
                if context_messages < 0 or context_messages > 50:
                    return Response(
                        {'error': 'context_messages must be between 0 and 50'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Update session settings
                session.settings['context_messages'] = context_messages
                session.save(update_fields=['settings'])
                
                return Response({
                    'context_messages': context_messages,
                    'message': f"Conversation context set to {context_messages} messages"
                })
                
            except (ValueError, TypeError):
                return Response(
                    {'error': 'context_messages must be a valid integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'context_messages parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ChatHealthView(APIView):
    """Health check endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'message': 'NeuralProtocol Chat API is running'
        })

