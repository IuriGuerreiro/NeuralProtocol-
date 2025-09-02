"""
MCP SEE (StreamableHTTP & SSE) - HTTP and Server-Sent Events Transport Manager

This module handles HTTP and SSE (Server-Sent Events) connections for MCP servers,
providing transport management for web-based MCP server communications.
Uses langchain_mcp_adapters for streamable_http and sse, custom aiohttp for http.
"""

import asyncio
import json
import logging
import aiohttp
import time
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack
from urllib.parse import urljoin
from datetime import datetime

from pydantic import BaseModel, Field, ValidationError
from langchain_mcp_adapters.client import MultiServerMCPClient


class HttpServerConfig(BaseModel):
    """Pydantic model for HTTP/SSE server configuration."""
    transport: str = Field(..., description="Transport type (http, sse, or streamable_http)")
    url: str = Field(..., description="Base URL for the server")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers")
    timeout: Optional[int] = Field(30, description="Request timeout in seconds")
    ssl_verify: Optional[bool] = Field(True, description="Verify SSL certificates")


class HttpMCPServer:
    """Manages HTTP/SSE MCP server connections."""

    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        self.name = name
        try:
            self.config = HttpServerConfig(**config)
        except ValidationError as e:
            logging.error(f"Invalid HTTP server configuration for {name}: {e}")
            raise
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_connected = False
        self._cleanup_lock = asyncio.Lock()
        self.exit_stack = AsyncExitStack()
        self.base_url = self.config.url.rstrip('/')
        self.mcp_session_id: Optional[str] = None
        
        # For langchain adapters
        self._langchain_client: Optional[MultiServerMCPClient] = None
        self._langchain_tools: List[Any] = []

    async def initialize(self) -> None:
        """Initialize the HTTP/SSE server connection."""
        try:
            transport = self.config.transport.lower()
            
            if transport in ["sse", "streamable_http"]:
                # Use langchain adapters for SSE and streamable_http
                await self._initialize_langchain()
            else:
                # Use custom aiohttp for regular http
                await self._initialize_aiohttp()
                
        except Exception as e:
            logging.error(f"❌ Error initializing HTTP/SSE server {self.name}: {e}")
            await self.cleanup()
            raise

    async def _initialize_langchain(self) -> None:
        """Initialize using langchain_mcp_adapters."""
        try:
            server_config = {
                self.name: {
                    "url": self.config.url,
                    "transport": self.config.transport,
                    "headers": self.config.headers
                }
            }
            
            self._langchain_client = MultiServerMCPClient(server_config)
            self.is_connected = True
            logging.info(f"✅ HTTP/SSE Server {self.name} ({self.config.transport}) initialized with langchain adapters")
            
        except Exception as e:
            logging.error(f"❌ Error initializing langchain client for {self.name}: {e}")
            raise

    async def _initialize_aiohttp(self) -> None:
        """Initialize using custom aiohttp implementation."""
        try:
            connector = aiohttp.TCPConnector(ssl=self.config.ssl_verify)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            headers = self.config.headers or {}
            headers.setdefault('User-Agent', 'NeuralProtocol-MCP-Client/1.0')
            headers.setdefault('Accept', 'application/json')
            
            self.session = await self.exit_stack.enter_async_context(
                aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=headers
                )
            )
            
            await self._test_connection()
            self.is_connected = True
            logging.info(f"✅ HTTP/SSE Server {self.name} ({self.config.transport}) initialized with aiohttp")
            
        except Exception as e:
            logging.error(f"❌ Error initializing aiohttp for {self.name}: {e}")
            raise

    async def _test_connection(self) -> None:
        """Test connection to the server (aiohttp only)."""
        try:
            # Try different health endpoints
            health_endpoints = ["/", "/health", "/status"]
            
            for endpoint in health_endpoints:
                try:
                    test_url = urljoin(self.base_url, endpoint)
                    async with self.session.get(test_url) as response:
                        if response.status == 200:
                            logging.info(f"🔗 Connection to {self.name} verified at {endpoint}")
                            # Check for MCP session ID in headers
                            mcp_session_id = response.headers.get('mcp-session-id')
                            if mcp_session_id:
                                self.mcp_session_id = mcp_session_id
                                logging.info(f"🔗 MCP session ID captured: {mcp_session_id}")
                            return
                        elif response.status < 500:  # Client errors are acceptable
                            logging.info(f"🔗 Connection to {self.name} verified at {endpoint} (status: {response.status})")
                            return
                except Exception as e:
                    continue
            
            # If all endpoints failed, try a basic GET to the base URL
            try:
                async with self.session.get(self.base_url) as response:
                    logging.info(f"🔗 Connection to {self.name} verified (status: {response.status})")
                    return
            except Exception as e:
                logging.warning(f"⚠️ Connection test failed for {self.name}: {e}")
                
        except Exception as e:
            logging.warning(f"⚠️ Connection test failed for {self.name}: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the HTTP/SSE server."""
        if not self.is_connected:
            raise RuntimeError(f"Server {self.name} not initialized")
        
        if self._langchain_client:
            # Use langchain adapters
            return await self._call_tool_langchain(tool_name, arguments)
        else:
            # Use custom aiohttp
            return await self._call_tool_aiohttp(tool_name, arguments)

    async def _call_tool_langchain(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call tool using langchain adapters."""
        try:
            tools = await self._langchain_client.get_tools()
            
            # Find the specific tool
            for tool in tools:
                if tool.name == tool_name:
                    logging.info(f"🔧 Calling tool {tool_name} on {self.name} (langchain)")
                    result = await tool.ainvoke(arguments)
                    logging.info(f"✅ Tool {tool_name} executed successfully on {self.name}: {result}")
                    return result
            
            raise RuntimeError(f"Tool {tool_name} not found on server {self.name}")
            
        except Exception as e:
            logging.error(f"❌ Error calling tool {tool_name} on {self.name}: {e}")
            raise

    async def _call_tool_aiohttp(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call tool using custom aiohttp implementation."""
        if not self.session:
            raise RuntimeError(f"Session not initialized for {self.name}")
        
        # Try different tool call endpoints
        tool_endpoints = [f'/tools/{tool_name}', f'/api/tools/{tool_name}', f'/mcp/tools/{tool_name}']
        
        for endpoint in tool_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                payload = {
                    "tool": tool_name,
                    "arguments": arguments,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add MCP session ID if available
                headers = {}
                if self.mcp_session_id:
                    headers['mcp-session-id'] = self.mcp_session_id
                
                logging.info(f"🔧 Calling tool {tool_name} on {self.name} at: {url}")
                logging.info(f"📡 Request payload: {payload}")
                
                async with self.session.post(url, json=payload, headers=headers) as response:
                    logging.info(f"📡 Response from {url}: Status {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        logging.info(f"✅ Tool {tool_name} executed successfully on {self.name}: {result}")
                        return result
                    elif response.status == 404:
                        logging.info(f"❌ Endpoint {endpoint} not found (404) for tool {tool_name} on {self.name}")
                        continue  # Try next endpoint
                    else:
                        error_text = await response.text()
                        logging.warning(f"⚠️ Unexpected response for tool {tool_name} on {self.name} at {endpoint}: {response.status} - {error_text}")
                        continue
            except Exception as e:
                logging.error(f"❌ Error calling tool {tool_name} on {self.name} at {endpoint}: {e}")
                continue
        
        # If all endpoints failed, try MCP protocol
        logging.info(f"🔍 Trying MCP protocol for tool {tool_name} on {self.name} at: {self.base_url}")
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            headers = {}
            if self.mcp_session_id:
                headers['mcp-session-id'] = self.mcp_session_id
            
            logging.info(f"📡 Sending MCP request to {self.name}: {mcp_request}")
            async with self.session.post(self.base_url, json=mcp_request, headers=headers) as response:
                logging.info(f"📡 MCP response from {self.name}: Status {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    logging.info(f"✅ Tool {tool_name} executed via MCP protocol on {self.name}: {result}")
                    return result.get('result', result)
                else:
                    error_text = await response.text()
                    logging.error(f"❌ MCP protocol failed for tool {tool_name} on {self.name}: {response.status} - {error_text}")
                    raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")
        except Exception as e:
            logging.error(f"❌ MCP protocol error for tool {tool_name} on {self.name}: {e}")
            raise aiohttp.ClientError(f"All tool call methods failed: {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the server."""
        if not self.is_connected:
            raise RuntimeError(f"Server {self.name} not initialized")
        
        if self._langchain_client:
            # Use langchain adapters
            return await self._list_tools_langchain()
        else:
            # Use custom aiohttp
            return await self._list_tools_aiohttp()

    async def _list_tools_langchain(self) -> List[Dict[str, Any]]:
        """Get tools using langchain adapters."""
        try:
            tools = await self._langchain_client.get_tools()
            tools_data = []
            
            for tool in tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": getattr(tool, 'args_schema', {})
                }
                tools_data.append(tool_info)
            
            logging.info(f"✅ Found {len(tools_data)} tools from {self.name} (langchain)")
            return tools_data
            
        except Exception as e:
            logging.error(f"❌ Error listing tools from server {self.name}: {e}")
            return []

    async def _list_tools_aiohttp(self) -> List[Dict[str, Any]]:
        """Get tools using custom aiohttp implementation."""
        if not self.session:
            raise RuntimeError(f"Session not initialized for {self.name}")
        
        try:
            # Try different tool endpoints
            tool_endpoints = ["/tools", "/api/tools", "/mcp/tools"]
            
            for endpoint in tool_endpoints:
                try:
                    tools_url = urljoin(self.base_url, endpoint)
                    headers = {}
                    if self.mcp_session_id:
                        headers['mcp-session-id'] = self.mcp_session_id
                    
                    logging.info(f"🔍 Trying to get tools from {self.name} at: {tools_url}")
                    async with self.session.get(tools_url, headers=headers) as response:
                        logging.info(f"📡 Response from {tools_url}: Status {response.status}")
                        
                        if response.status == 200:
                            tools_data = await response.json()
                            logging.info(f"📋 Tools data received from {self.name}: {tools_data}")
                            
                            if isinstance(tools_data, dict) and 'tools' in tools_data:
                                tools_list = tools_data['tools']
                                logging.info(f"✅ Found {len(tools_list)} tools in 'tools' field from {self.name}")
                                return tools_list
                            elif isinstance(tools_data, list):
                                logging.info(f"✅ Found {len(tools_data)} tools in list from {self.name}")
                                return tools_data
                            else:
                                logging.warning(f"⚠️ Unexpected tools data format from {self.name}: {type(tools_data)}")
                                return []
                        elif response.status == 404:
                            logging.info(f"❌ Endpoint {endpoint} not found (404) for {self.name}")
                            continue  # Try next endpoint
                        else:
                            response_text = await response.text()
                            logging.warning(f"⚠️ Unexpected response from {self.name} at {endpoint}: {response.status} - {response_text}")
                            continue
                except Exception as e:
                    logging.error(f"❌ Error trying endpoint {endpoint} for {self.name}: {e}")
                    continue
            
            # If no tools endpoint found, try MCP protocol
            logging.info(f"🔍 Trying MCP protocol for {self.name} at: {self.base_url}")
            try:
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                }
                
                headers = {}
                if self.mcp_session_id:
                    headers['mcp-session-id'] = self.mcp_session_id
                
                logging.info(f"📡 Sending MCP request to {self.name}: {mcp_request}")
                async with self.session.post(self.base_url, json=mcp_request, headers=headers) as response:
                    logging.info(f"📡 MCP response from {self.name}: Status {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        logging.info(f"📋 MCP response data from {self.name}: {result}")
                        
                        tools = result.get('result', {}).get('tools', [])
                        logging.info(f"✅ Found {len(tools)} tools via MCP protocol from {self.name}")
                        return tools
                    else:
                        response_text = await response.text()
                        logging.warning(f"⚠️ MCP protocol failed for {self.name}: {response.status} - {response_text}")
                        return []
            except Exception as e:
                logging.error(f"❌ MCP protocol error for {self.name}: {e}")
                return []
                    
        except Exception as e:
            logging.error(f"❌ Error listing tools from server {self.name}: {e}")
            return []

    def is_initialized(self) -> bool:
        """Check if the server is initialized."""
        return self.is_connected and (self.session is not None or self._langchain_client is not None)

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                if self.session:
                    await self.exit_stack.aclose()
                    self.session = None
                
                if self._langchain_client:
                    self._langchain_client = None
                
                self.is_connected = False
                self.mcp_session_id = None
                logging.info(f"🧹 HTTP/SSE Server {self.name} cleaned up")
            except Exception as e:
                logging.error(f"❌ Error during cleanup of {self.name}: {e}")


class HttpMCPStudio:
    """Studio for managing multiple HTTP/SSE MCP servers."""
    
    def __init__(self):
        self.servers: List[HttpMCPServer] = []
        
    def add_server(self, name: str, server_config: Dict[str, Any]) -> None:
        """Add a new HTTP/SSE MCP server."""
        try:
            server = HttpMCPServer(name, server_config)
            self.servers.append(server)
            logging.info(f"✅ Added HTTP/SSE server: {name}")
        except ValidationError as e:
            logging.error(f"❌ Invalid config for server {name}: {e}")
            raise
    
    def load_servers_from_config(self, config_data: Dict[str, Any]) -> None:
        """Load HTTP/SSE servers from configuration data."""
        if "mcpServers" not in config_data:
            return
            
        for name, srv_config in config_data["mcpServers"].items():
            try:
                transport = srv_config.get("transport", "").lower()
                if transport in ["http", "sse", "streamable_http"]:
                    self.add_server(name, srv_config)
            except Exception as e:
                logging.error(f"❌ Error loading server {name}: {e}")
    
    async def initialize_all_servers(self) -> None:
        """Initialize all HTTP/SSE servers."""
        for server in self.servers:
            try:
                await server.initialize()
            except Exception as e:
                logging.error(f"❌ Failed to initialize server {server.name}: {e}")
    
    async def cleanup_all_servers(self) -> None:
        """Clean up all HTTP/SSE servers."""
        for server in reversed(self.servers):
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"⚠️ Cleanup warning: {e}")
    
    def get_initialized_servers(self) -> List[HttpMCPServer]:
        """Get list of initialized HTTP/SSE servers."""
        return [server for server in self.servers if server.is_initialized()]
    
    async def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get tools from all initialized HTTP/SSE servers."""
        all_tools = {}
        for server in self.get_initialized_servers():
            try:
                tools = await server.list_tools()
                all_tools[server.name] = tools
                logging.info(f"📋 Loaded {len(tools)} tools from {server.name}")
            except Exception as e:
                logging.error(f"❌ Error loading tools from {server.name}: {e}")
                all_tools[server.name] = []
        return all_tools


def get_supported_transports() -> List[str]:
    """Get list of supported transport types."""
    return ["http", "sse", "streamable_http"] 