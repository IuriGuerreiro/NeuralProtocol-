"""
Tools Manager - Tool Loading, Management and Execution

This module handles loading tools from MCP servers and custom tools,
managing tool execution, and providing a unified interface for tools.
"""

import logging
from typing import Any, List, Dict, Optional
from datetime import datetime

from langchain_mcp_adapters.tools import load_mcp_tools
from pydantic import BaseModel, Field, ValidationError

from utils.mcp_studio import MCPStudio, MCPServer
from utils.mcp_see_http import HttpMCPStudio, HttpMCPServer


class ToolCall(BaseModel):
    """Pydantic model for validating tool calls."""
    tool: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(..., description="Arguments for the tool")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp of the tool call")


class ToolResult(BaseModel):
    """Pydantic model for tool execution results."""
    tool_name: str = Field(..., description="Name of the executed tool")
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Any = Field(..., description="Result of the tool execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp of the result")


class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    source: str = Field(..., description="Source of the tool (mcp_server:name, custom, or see)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    category: str = Field(default="unknown", description="Tool category (mcp, custom, see)")


class ToolsManager:
    """Manages tools from MCP servers and custom tools."""
    
    def __init__(self, mcp_studio: MCPStudio, http_mcp_studio: Optional[HttpMCPStudio] = None):
        self.mcp_studio = mcp_studio
        self.http_mcp_studio = http_mcp_studio or HttpMCPStudio()
        self.mcp_tools: List[Any] = []
        self.http_tools: List[Any] = []
        self.custom_tools: List[Any] = []
        self.see_tools: List[Any] = []
        self.all_tools: List[Any] = []
        self.tool_info: Dict[str, ToolInfo] = {}
        self.approval_enabled: bool = True  # Enable tool approval by default
        
    def set_approval_mode(self, enabled: bool) -> None:
        """Enable or disable tool approval mode."""
        self.approval_enabled = enabled
        status = "enabled" if enabled else "disabled"
        logging.info(f"🔐 Tool approval mode {status}")
        
    def _display_tool_approval_request(self, tool_name: str, arguments: Dict[str, Any], tool_info: ToolInfo) -> None:
        """Display tool approval request with details."""
        print(f"\n🔧 Tool Approval Request:")
        print(f"📋 Tool: {tool_name}")
        print(f"📝 Description: {tool_info.description}")
        print(f"🌐 Source: {tool_info.source}")
        print(f"⚙️ Arguments: {arguments}")
        print(f"\n❓ Do you want to approve this tool execution?")
        print(f"   1 - ✅ Approve")
        print(f"   2 - ❌ Disapprove")
        
    def _get_user_approval(self) -> bool:
        """Get user approval for tool execution."""
        while True:
            try:
                choice = input("\n💬 Enter your choice (1 or 2): ").strip()
                if choice == "1":
                    print("✅ Tool execution approved!")
                    return True
                elif choice == "2":
                    print("❌ Tool execution disapproved!")
                    return False
                else:
                    print("⚠️ Invalid choice. Please enter 1 (approve) or 2 (disapprove).")
            except KeyboardInterrupt:
                print("\n❌ Tool execution cancelled by user.")
                return False
            except Exception as e:
                print(f"⚠️ Error reading input: {e}")
                return False
        
    async def load_mcp_tools(self) -> None:
        """Load tools from all initialized MCP servers."""
        self.mcp_tools = []
        
        for server in self.mcp_studio.get_initialized_servers():
            try:
                tools = await self._load_tools_from_server(server)
                self.mcp_tools.extend(tools)
                
                # Store tool info for each tool
                for tool in tools:
                    tool_name = getattr(tool, 'name', str(tool))
                    self.tool_info[tool_name] = ToolInfo(
                        name=tool_name,
                        description=getattr(tool, 'description', 'No description available'),
                        source=f"mcp_server:{server.name}",
                        parameters=getattr(tool, 'parameters', {}),
                        category="mcp"
                    )
                    
            except Exception as e:
                logging.error(f"❌ Error loading tools from server {server.name}: {e}")
        
        logging.info(f"🔧 Loaded {len(self.mcp_tools)} MCP tools from {len(self.mcp_studio.get_initialized_servers())} servers")
    
    async def load_http_tools(self) -> None:
        """Load tools from all initialized HTTP/SSE MCP servers."""
        self.http_tools = []
        
        for server in self.http_mcp_studio.get_initialized_servers():
            try:
                transport = server.config.transport.lower()
                
                if transport in ["sse", "streamable_http"]:
                    # Use langchain adapters for SSE and streamable_http
                    await self._load_langchain_tools(server)
                else:
                    # Use custom aiohttp for regular http
                    await self._load_aiohttp_tools(server)
                        
            except Exception as e:
                logging.error(f"❌ Error loading tools from HTTP server {server.name}: {e}")
        
        logging.info(f"🔧 Loaded {len(self.http_tools)} HTTP/SSE tools from {len(self.http_mcp_studio.get_initialized_servers())} servers")

    async def _load_langchain_tools(self, server: HttpMCPServer) -> None:
        """Load tools from server using langchain adapters."""
        try:
            tools = await server._langchain_client.get_tools()
            
            # Add tools directly (they're already in langchain format)
            self.http_tools.extend(tools)
            
            # Store tool info for each tool
            for tool in tools:
                tool_name = tool.name
                self.tool_info[tool_name] = ToolInfo(
                    name=tool_name,
                    description=tool.description,
                    source=f"http_server:{server.name}",
                    parameters=getattr(tool, 'args_schema', {}),
                    category="http"
                )
            
            logging.info(f"🔧 Loaded {len(tools)} tools from {server.name} (langchain adapters)")
            
        except Exception as e:
            logging.error(f"❌ Error loading langchain tools from {server.name}: {e}")

    async def _load_aiohttp_tools(self, server: HttpMCPServer) -> None:
        """Load tools from server using custom aiohttp implementation."""
        try:
            tools_data = await server.list_tools()
            
            # Create langchain-compatible tools for HTTP servers
            for tool_data in tools_data:
                tool = await self._create_http_tool(server, tool_data)
                if tool:
                    self.http_tools.append(tool)
                    
                    # Store tool info
                    tool_name = tool_data.get('name', f'{server.name}_tool')
                    self.tool_info[tool_name] = ToolInfo(
                        name=tool_name,
                        description=tool_data.get('description', 'HTTP/SSE MCP tool'),
                        source=f"http_server:{server.name}",
                        parameters=tool_data.get('parameters', {}),
                        category="http"
                    )
            
            logging.info(f"🔧 Loaded {len(tools_data)} tools from {server.name} (aiohttp)")
            
        except Exception as e:
            logging.error(f"❌ Error loading aiohttp tools from {server.name}: {e}")

    async def _create_http_tool(self, server: HttpMCPServer, tool_data: Dict[str, Any]) -> Any:
        """Create a langchain-compatible tool for HTTP/SSE servers."""
        from langchain.tools import BaseTool
        
        # Capture the server and tool_data in a closure
        server_instance = server
        tool_name = tool_data.get('name', 'http_tool')
        tool_description = tool_data.get('description', 'HTTP/SSE MCP tool')
        
        class HttpMCPTool(BaseTool):
            name: str = tool_name
            description: str = tool_description
            
            def _run(self, **kwargs) -> str:
                """Synchronous run method."""
                raise NotImplementedError("Use async version")
            
            async def _arun(self, **kwargs) -> str:
                """Asynchronous run method."""
                try:
                    result = await server_instance.call_tool(tool_name, kwargs)
                    return str(result)
                except Exception as e:
                    return f"Error executing HTTP tool {tool_name}: {e}"
        
        return HttpMCPTool()
        
    async def _load_tools_from_server(self, server: MCPServer) -> List[Any]:
        """Load tools from a specific MCP server.
        
        Args:
            server: The MCP server to load tools from
            
        Returns:
            List of tools from the server
        """
        if not server.session:
            raise RuntimeError(f"Server {server.name} not initialized")

        try:
            tools = await load_mcp_tools(server.session)
            logging.info(f"📋 Loaded {len(tools)} tools from server {server.name}")
            return tools
        except Exception as e:
            logging.error(f"❌ Error loading tools from server {server.name}: {e}")
            return []
    
    def add_custom_tools(self, tools: List[Any]) -> None:
        """Add custom tools to the manager.
        
        Args:
            tools: List of custom tools to add
        """
        for tool in tools:
            self.custom_tools.append(tool)
            tool_name = getattr(tool, 'name', str(tool))
            self.tool_info[tool_name] = ToolInfo(
                name=tool_name,
                description=getattr(tool, 'description', 'Custom tool - no description available'),
                source="custom",
                parameters=getattr(tool, 'parameters', {}),
                category="custom"
            )
        
        logging.info(f"🔧 Added {len(tools)} custom tools")
    
    def add_see_tools(self, tools: List[Any]) -> None:
        """Add SEE tools to the manager.
        
        Args:
            tools: List of SEE tools to add
        """
        for tool in tools:
            self.see_tools.append(tool)
            tool_name = getattr(tool, 'name', str(tool))
            self.tool_info[tool_name] = ToolInfo(
                name=tool_name,
                description=getattr(tool, 'description', 'SEE tool - vision and analysis'),
                source="see",
                parameters=getattr(tool, 'parameters', {}),
                category="see"
            )
        
        logging.info(f"🔧 Added {len(tools)} SEE tools")
    
    def get_all_tools(self) -> List[Any]:
        """Get all tools (MCP + HTTP + custom + SEE).
        
        Returns:
            List of all available tools
        """
        all_tools = self.mcp_tools + self.http_tools + self.custom_tools + self.see_tools
        return all_tools
    
    def get_tool_names(self) -> List[str]:
        """Get names of all available tools.
        
        Returns:
            List of tool names
        """
        return [getattr(tool, 'name', str(tool)) for tool in self.get_all_tools()]
    
    def get_tool_info_dict(self) -> Dict[str, ToolInfo]:
        """Get tool information dictionary.
        
        Returns:
            Dictionary mapping tool names to ToolInfo objects
        """
        return self.tool_info
    
    def find_tool_by_name(self, tool_name: str) -> Optional[Any]:
        """Find a tool by name.
        
        Args:
            tool_name: Name of the tool to find
            
        Returns:
            The tool object if found, None otherwise
        """
        for tool in self.get_all_tools():
            if getattr(tool, 'name', str(tool)) == tool_name:
                return tool
        return None
    
    def get_tools_by_source(self, source_type: str, source_name: Optional[str] = None) -> List[Any]:
        """Get tools by source type and optionally source name.
        
        Args:
            source_type: Type of source ('mcp_server', 'http_server', 'custom', or 'see')
            source_name: Name of the specific source (server name for MCP/HTTP tools)
            
        Returns:
            List of tools matching the criteria
        """
        matching_tools = []
        
        for tool_name, tool_info in self.tool_info.items():
            if source_type == "custom" and tool_info.source == "custom":
                tool = self.find_tool_by_name(tool_name)
                if tool:
                    matching_tools.append(tool)
            elif source_type == "see" and tool_info.source == "see":
                tool = self.find_tool_by_name(tool_name)
                if tool:
                    matching_tools.append(tool)
            elif source_type == "mcp_server":
                if source_name:
                    if tool_info.source == f"mcp_server:{source_name}":
                        tool = self.find_tool_by_name(tool_name)
                        if tool:
                            matching_tools.append(tool)
                else:
                    if tool_info.source.startswith("mcp_server:"):
                        tool = self.find_tool_by_name(tool_name)
                        if tool:
                            matching_tools.append(tool)
            elif source_type == "http_server":
                if source_name:
                    if tool_info.source == f"http_server:{source_name}":
                        tool = self.find_tool_by_name(tool_name)
                        if tool:
                            matching_tools.append(tool)
                else:
                    if tool_info.source.startswith("http_server:"):
                        tool = self.find_tool_by_name(tool_name)
                        if tool:
                            matching_tools.append(tool)
        
        return matching_tools
    
    def validate_tool_call(self, tool_call_data: Dict[str, Any]) -> ToolCall:
        """Validate a tool call using Pydantic.
        
        Args:
            tool_call_data: Dictionary containing tool call data
            
        Returns:
            Validated ToolCall object
            
        Raises:
            ValidationError: If the tool call data is invalid
        """
        try:
            return ToolCall(**tool_call_data)
        except ValidationError as e:
            logging.error(f"❌ Invalid tool call data: {e}")
            raise
    
    async def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call and return the result.
        
        Args:
            tool_call: Validated tool call to execute
            
        Returns:
            ToolResult object with execution results
        """
        try:
            tool = self.find_tool_by_name(tool_call.tool)
            if not tool:
                error_msg = f"Tool '{tool_call.tool}' not found"
                logging.error(f"❌ {error_msg}")
                return ToolResult(
                    tool_name=tool_call.tool,
                    success=False,
                    result=None,
                    error=error_msg
                )
            
            # Get tool info for approval display
            tool_info = self.tool_info.get(tool_call.tool)
            
            # Check if approval is required
            if self.approval_enabled:
                self._display_tool_approval_request(tool_call.tool, tool_call.arguments, tool_info)
                if not self._get_user_approval():
                    return ToolResult(
                        tool_name=tool_call.tool,
                        success=False,
                        result=None,
                        error="Tool execution disapproved by user"
                    )
            
            # Execute the tool
            logging.info(f"🔧 Executing tool: {tool_call.tool}")
            logging.debug(f"📝 Arguments: {tool_call.arguments}")
            
            # For langchain tools, use invoke method
            if hasattr(tool, 'invoke'):
                result = await tool.ainvoke(tool_call.arguments) if hasattr(tool, 'ainvoke') else tool.invoke(tool_call.arguments)
            elif hasattr(tool, 'run'):
                result = await tool.arun(tool_call.arguments) if hasattr(tool, 'arun') else tool.run(tool_call.arguments)
            elif callable(tool):
                result = await tool(**tool_call.arguments) if hasattr(tool, '__await__') else tool(**tool_call.arguments)
            else:
                error_msg = f"Tool '{tool_call.tool}' is not executable"
                logging.error(f"❌ {error_msg}")
                return ToolResult(
                    tool_name=tool_call.tool,
                    success=False,
                    result=None,
                    error=error_msg
                )
            
            logging.info(f"✅ Tool '{tool_call.tool}' executed successfully")
            return ToolResult(
                tool_name=tool_call.tool,
                success=True,
                result=result,
                error=None
            )
            
        except Exception as e:
            error_msg = f"Error executing tool '{tool_call.tool}': {str(e)}"
            logging.error(f"❌ {error_msg}")
            return ToolResult(
                tool_name=tool_call.tool,
                success=False,
                result=None,
                error=error_msg
            )
    
    def get_tools_summary(self) -> Dict[str, Any]:
        """Get a summary of all available tools.
        
        Returns:
            Dictionary with tools summary
        """
        mcp_tools_by_server = {}
        http_tools_by_server = {}
        custom_tools_count = 0
        see_tools_count = 0
        
        for tool_name, tool_info in self.tool_info.items():
            if tool_info.source == "custom":
                custom_tools_count += 1
            elif tool_info.source == "see":
                see_tools_count += 1
            elif tool_info.source.startswith("mcp_server:"):
                server_name = tool_info.source.split(":")[1]
                if server_name not in mcp_tools_by_server:
                    mcp_tools_by_server[server_name] = []
                mcp_tools_by_server[server_name].append(tool_name)
            elif tool_info.source.startswith("http_server:"):
                server_name = tool_info.source.split(":")[1]
                if server_name not in http_tools_by_server:
                    http_tools_by_server[server_name] = []
                http_tools_by_server[server_name].append(tool_name)
        
        return {
            "total_tools": len(self.tool_info),
            "mcp_tools": {
                "total": len(self.mcp_tools),
                "by_server": mcp_tools_by_server
            },
            "http_tools": {
                "total": len(self.http_tools),
                "by_server": http_tools_by_server
            },
            "custom_tools": {
                "total": custom_tools_count
            },
            "see_tools": {
                "total": see_tools_count
            },
            "tool_names": list(self.tool_info.keys())
        }
    
    def print_tools_summary(self) -> None:
        """Print a formatted summary of all available tools."""
        summary = self.get_tools_summary()
        
        print(f"\n🔧 Tools Summary:")
        print(f"📊 Total tools: {summary['total_tools']}")
        
        if summary['mcp_tools']['total'] > 0:
            print(f"\n🌐 MCP Tools ({summary['mcp_tools']['total']}):")
            for server_name, tools in summary['mcp_tools']['by_server'].items():
                print(f"  📋 {server_name}: {', '.join(tools)}")
        
        if summary['http_tools']['total'] > 0:
            print(f"\n🌍 HTTP/SSE Tools ({summary['http_tools']['total']}):")
            for server_name, tools in summary['http_tools']['by_server'].items():
                print(f"  📋 {server_name}: {', '.join(tools)}")
        
        if summary['custom_tools']['total'] > 0:
            custom_tools = [name for name, info in self.tool_info.items() if info.source == "custom"]
            print(f"\n🛠️ Custom Tools ({summary['custom_tools']['total']}):")
            print(f"  📋 {', '.join(custom_tools)}")
        
        if summary['see_tools']['total'] > 0:
            see_tools = [name for name, info in self.tool_info.items() if info.source == "see"]
            print(f"\n👁️ SEE Tools ({summary['see_tools']['total']}):")
            print(f"  📋 {', '.join(see_tools)}")
        
        if summary['total_tools'] == 0:
            print("⚠️ No tools available")
