"""
Global Tools Manager for Django Chat Application

This module provides a singleton pattern for managing MCP servers and tools
that are initialized once at Django startup and reused across all chat sessions.
"""

import asyncio
import logging
from typing import Optional
from threading import Lock

from chat.utils.mcp_studio import MCPStudio, Configuration
from chat.utils.tools_manager import ToolsManager
from chat.utils.custom_tools import get_all_custom_tools
from chat.utils.mcp_see_http import HttpMCPStudio


class GlobalToolsManager:
    """Singleton class for managing global MCP servers and tools."""
    
    _instance: Optional['GlobalToolsManager'] = None
    _lock: Lock = Lock()
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.config = Configuration()
            self.mcp_studio = MCPStudio(self.config)
            self.http_mcp_studio = HttpMCPStudio()
            self.tools_manager = ToolsManager(self.mcp_studio, self.http_mcp_studio)
            import os
            backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_file = os.path.join(backend_root, "servers_config_minimal.json")
            self._initialized = True
            
            logging.info("🔧 Global Tools Manager created")
    
    async def initialize_all_async(self) -> None:
        """Initialize MCP servers and tools asynchronously."""
        try:
            await self.initialize_mcp_servers()
            await self.initialize_tools()
            logging.info("🌟 Global Tools Manager fully initialized")
        except Exception as e:
            logging.error(f"❌ Error initializing global tools: {e}")
            # Don't raise - allow Django to start even if MCP fails
            # Custom tools will still be available
            logging.info("🔧 Continuing with custom tools only")
    
    async def initialize_mcp_servers(self) -> None:
        """Initialize MCP servers from configuration."""
        try:
            # Load configuration data
            server_config = self.config.load_config(self.config_file)
            
            # Initialize stdio MCP servers
            self.mcp_studio.load_servers_from_config(self.config_file)
            await self.mcp_studio.initialize_all_servers()
            
            # Initialize HTTP/SSE MCP servers
            self.http_mcp_studio.load_servers_from_config(server_config)
            await self.http_mcp_studio.initialize_all_servers()
            
            stdio_servers = self.mcp_studio.get_initialized_servers()
            http_servers = self.http_mcp_studio.get_initialized_servers()
            
            logging.info(f"✅ Global: Initialized {len(stdio_servers)} STDIO servers and {len(http_servers)} HTTP/SSE servers")
            
        except Exception as e:
            logging.error(f"❌ Error initializing global MCP servers: {e}")
            raise
    
    async def initialize_tools(self) -> None:
        """Initialize MCP, HTTP/SSE, and custom tools."""
        try:
            # Load MCP tools (stdio) - may fail silently
            try:
                await self.tools_manager.load_mcp_tools()
                logging.info("✅ MCP tools loaded")
            except Exception as e:
                logging.warning(f"⚠️ MCP tools failed to load: {e}")
            
            # Load HTTP/SSE tools - may fail silently  
            try:
                await self.tools_manager.load_http_tools()
                logging.info("✅ HTTP tools loaded")
            except Exception as e:
                logging.warning(f"⚠️ HTTP tools failed to load: {e}")
            
            # Add custom tools - should always work
            try:
                custom_tools = get_all_custom_tools()
                self.tools_manager.add_custom_tools(custom_tools)
                logging.info(f"✅ Custom tools loaded: {len(custom_tools)}")
            except Exception as e:
                logging.warning(f"⚠️ Custom tools failed to load: {e}")
            
            # Log tools summary
            self.tools_manager.print_tools_summary()
            
        except Exception as e:
            logging.error(f"❌ Error initializing tools: {e}")
            # Don't raise - at least custom tools should work
    
    def get_all_tools(self):
        """Get all available tools from the global tools manager."""
        return self.tools_manager.get_all_tools()
    
    def get_tools_summary(self):
        """Get tools summary from the global tools manager."""
        return self.tools_manager.get_tools_summary()
    
    def set_approval_mode(self, enabled: bool):
        """Set approval mode for tools."""
        self.tools_manager.set_approval_mode(enabled)
    
    @property
    def approval_enabled(self):
        """Check if approval mode is enabled."""
        return self.tools_manager.approval_enabled


def initialize_global_tools():
    """Synchronous wrapper to initialize global tools."""
    def run_async_init():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            global_tools = GlobalToolsManager()
            loop.run_until_complete(global_tools.initialize_all_async())
        finally:
            loop.close()
    
    import threading
    thread = threading.Thread(target=run_async_init)
    thread.start()
    thread.join()


# Global instance
global_tools_manager = GlobalToolsManager()