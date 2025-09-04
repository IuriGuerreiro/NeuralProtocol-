"""
MCP Studio - MCP Server Management Utilities

This module handles MCP server connections, configurations, and management.
"""

import asyncio
import json
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field, ValidationError


class ServerConfig(BaseModel):
    """Pydantic model for server configuration."""
    transport: str = Field(default="stdio", description="Transport type (stdio or http)")
    command: Optional[str] = Field(None, description="Command to start the server (stdio only)")
    args: Optional[List[str]] = Field(None, description="Arguments for the server command (stdio only)")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables for the server")
    url: Optional[str] = Field(None, description="URL for HTTP servers")


class Configuration:
    """Manages configuration and environment variables for the MCP client."""

    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        self.load_env()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    @staticmethod
    def load_env() -> None:
        """Load environment variables from .env file."""
        load_dotenv()

    @staticmethod
    def load_config(file_path: str) -> Dict[str, Any]:
        """Load server configuration from JSON file.

        Args:
            file_path: Path to the JSON configuration file.

        Returns:
            Dict containing server configuration.

        Raises:
            FileNotFoundError: If configuration file doesn't exist.
            JSONDecodeError: If configuration file is invalid JSON.
        """
        with open(file_path, "r") as f:
            return json.load(f)

    @property
    def llm_api_key(self) -> str:
        """Get the LLM API key.

        Returns:
            The API key as a string.

        Raises:
            ValueError: If the API key is not found in environment variables.
        """
        if self.api_key:
            return self.api_key
        elif self.openai_api_key:
            return self.openai_api_key
        elif self.anthropic_api_key:
            return self.anthropic_api_key
        else:
            raise ValueError("No API key found in environment variables (GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)")

    def get_provider_config(self, provider: str) -> Dict[str, str]:
        """Get provider-specific configuration.
        
        Args:
            provider: The provider name (google_genai, openai, anthropic, etc.)
            
        Returns:
            Dict with provider configuration
            
        Raises:
            ValueError: If provider is not supported or API key is missing
        """
        provider_configs = {
            "google_genai": {
                "env_var": "GOOGLE_API_KEY",
                "api_key": self.api_key
            },
            "openai": {
                "env_var": "OPENAI_API_KEY", 
                "api_key": self.openai_api_key
            },
            "anthropic": {
                "env_var": "ANTHROPIC_API_KEY",
                "api_key": self.anthropic_api_key
            }
        }
        
        if provider not in provider_configs:
            raise ValueError(f"Unsupported provider: {provider}")
            
        config = provider_configs[provider]
        if not config["api_key"]:
            raise ValueError(f"{config['env_var']} not found in environment variables")
            
        return config


class MCPServer:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        self.name: str = name
        # Validate config using Pydantic
        try:
            self.config = ServerConfig(**config)
        except ValidationError as e:
            logging.error(f"Invalid server configuration for {name}: {e}")
            raise
        
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize(self) -> None:
        """Initialize the server connection."""
        if self.config.transport != "stdio":
            raise ValueError(f"Server {self.name} uses {self.config.transport} transport, but only stdio is supported")
        
        if not self.config.command:
            raise ValueError(f"Server {self.name} requires a command for stdio transport")
            
        command = shutil.which("npx") if self.config.command == "npx" else self.config.command
        if command is None:
            raise ValueError("The command must be a valid string and cannot be None.")

        server_params = StdioServerParameters(
            command=command,
            args=self.config.args or [],
            env={**os.environ, **self.config.env} if self.config.env else None,
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.session = session
            logging.info(f"✅ Server {self.name} initialized successfully")
        except Exception as e:
            logging.error(f"❌ Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
                logging.info(f"🧹 Server {self.name} cleaned up")
            except Exception as e:
                logging.error(f"❌ Error during cleanup of server {self.name}: {e}")

    def is_initialized(self) -> bool:
        """Check if the server is initialized."""
        return self.session is not None


class MCPStudio:
    """Studio for managing multiple MCP servers."""
    
    def __init__(self, config: Configuration):
        self.config = config
        self.servers: List[MCPServer] = []
        
    def add_server(self, name: str, server_config: Dict[str, Any]) -> None:
        """Add a new MCP server to the studio.
        
        Args:
            name: Name of the server
            server_config: Server configuration dictionary
        """
        try:
            server = MCPServer(name, server_config)
            self.servers.append(server)
            logging.info(f"✅ Added server: {name}")
        except ValidationError as e:
            logging.error(f"❌ Invalid config for server {name}: {e}")
            raise
    
    def load_servers_from_config(self, config_file: str) -> None:
        """Load servers from configuration file.
        
        Args:
            config_file: Path to the configuration file
        """
        server_config = self.config.load_config(config_file)
        
        for name, srv_config in server_config["mcpServers"].items():
            try:
                server_cfg = ServerConfig(**srv_config)
                if server_cfg.transport == "stdio":
                    self.add_server(name, srv_config)
                else:
                    logging.warning(f"⚠️ Skipping {server_cfg.transport} server: {name} (only stdio supported)")
            except ValidationError as e:
                logging.error(f"❌ Invalid config for server {name}: {e}")
                continue
    
    async def initialize_all_servers(self) -> None:
        """Initialize all servers."""
        for server in self.servers:
            try:
                await server.initialize()
            except Exception as e:
                logging.error(f"❌ Failed to initialize server {server.name}: {e}")
                await self.cleanup_all_servers()
                raise
    
    async def cleanup_all_servers(self) -> None:
        """Clean up all servers."""
        for server in reversed(self.servers):
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"⚠️ Warning during cleanup: {e}")
    
    def get_initialized_servers(self) -> List[MCPServer]:
        """Get list of initialized servers."""
        return [server for server in self.servers if server.is_initialized()]
    
    def get_server_by_name(self, name: str) -> Optional[MCPServer]:
        """Get server by name."""
        for server in self.servers:
            if server.name == name:
                return server
        return None



