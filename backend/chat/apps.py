"""
Django App Configuration for Chat Application

Handles initialization of global MCP servers and tools at Django startup.
"""

import logging
from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Configuration for the Chat application."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"
    verbose_name = "NeuralProtocol Chat System"
    
    def ready(self):
        """Initialize global tools when Django starts."""
        # Only run once during startup (not during migrations, tests, etc.)
        import os
        import sys
        from django.conf import settings
        
        # Skip initialization during migrations and tests
        if (
            'runserver' not in sys.argv and 
            'gunicorn' not in sys.argv[0] and
            'uwsgi' not in sys.argv[0]
        ):
            logging.info("🚫 Skipping MCP initialization (not running server)")
            return
        
        # Skip if already initialized
        if hasattr(settings, 'MCP_TOOLS_INITIALIZED'):
            logging.info("🔧 MCP Tools already initialized")
            return
        
        try:
            logging.info("🚀 Initializing Global MCP Tools at Django startup...")
            
            from .global_tools import initialize_global_tools
            initialize_global_tools()
            
            # Mark as initialized
            settings.MCP_TOOLS_INITIALIZED = True
            
            logging.info("✅ Global MCP Tools initialization completed")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize global MCP tools: {e}")
            # Don't raise - let Django start even if MCP fails
            # Tools will be initialized on first use
