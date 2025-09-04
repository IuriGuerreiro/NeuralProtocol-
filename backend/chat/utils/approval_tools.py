wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww"""
Approval Tools - Tools with built-in approval system

This module provides wrapper tools that require user approval before execution.
"""

import logging
from typing import Any, Dict, Optional
from langchain.tools import BaseTool


class ApprovalTool:
    """A tool wrapper that requires user approval before execution."""
    
    def __init__(self, original_tool: Any, tools_manager: Any):
        self.original_tool = original_tool
        self.tools_manager = tools_manager
        
        # Copy attributes from original tool
        self.name = getattr(original_tool, 'name', str(original_tool))
        self.description = getattr(original_tool, 'description', 'No description available')
        
        # Add approval indicator to description
        self.description = f"{self.description} (requires approval)"
    
    def _run(self, **kwargs) -> str:
        """Synchronous run method."""
        raise NotImplementedError("Use async version")
    
    async def _arun(self, **kwargs) -> str:
        """Asynchronous run method with approval."""
        # Get tool info for approval display
        tool_info = self.tools_manager.tool_info.get(self.name)
        
        # Display approval request
        self._display_approval_request(kwargs, tool_info)
        
        # Get user approval
        if not self._get_user_approval():
            return "Tool execution disapproved by user"
        
        # Execute the original tool
        try:
            if hasattr(self.original_tool, 'ainvoke'):
                result = await self.original_tool.ainvoke(kwargs)
            elif hasattr(self.original_tool, 'arun'):
                result = await self.original_tool.arun(kwargs)
            elif hasattr(self.original_tool, 'invoke'):
                result = self.original_tool.invoke(kwargs)
            elif hasattr(self.original_tool, 'run'):
                result = self.original_tool.run(kwargs)
            elif callable(self.original_tool):
                result = await self.original_tool(**kwargs) if hasattr(self.original_tool, '__await__') else self.original_tool(**kwargs)
            else:
                return f"Error: Tool {self.name} is not executable"
            
            return str(result)
        except Exception as e:
            return f"Error executing tool {self.name}: {e}"
    
    def _run(self, **kwargs) -> str:
        """Synchronous run method."""
        raise NotImplementedError("Use async version")
    
    async def _arun(self, **kwargs) -> str:
        """Asynchronous run method with approval."""
        # Get tool info for approval display
        tool_info = self.tools_manager.tool_info.get(self.name)
        
        # Display approval request
        self._display_approval_request(kwargs, tool_info)
        
        # Get user approval
        if not self._get_user_approval():
            return "Tool execution disapproved by user"
        
        # Execute the original tool
        try:
            if hasattr(self.original_tool, 'ainvoke'):
                result = await self.original_tool.ainvoke(kwargs)
            elif hasattr(self.original_tool, 'arun'):
                result = await self.original_tool.arun(kwargs)
            elif hasattr(self.original_tool, 'invoke'):
                result = self.original_tool.invoke(kwargs)
            elif hasattr(self.original_tool, 'run'):
                result = self.original_tool.run(kwargs)
            elif callable(self.original_tool):
                result = await self.original_tool(**kwargs) if hasattr(self.original_tool, '__await__') else self.original_tool(**kwargs)
            else:
                return f"Error: Tool {self.name} is not executable"
            
            return str(result)
        except Exception as e:
            return f"Error executing tool {self.name}: {e}"
    
    def _display_approval_request(self, arguments: Dict[str, Any], tool_info: Optional[Any]) -> None:
        """Display tool approval request with details."""
        print(f"\n🔧 Tool Approval Request:")
        print(f"📋 Tool: {self.name}")
        if tool_info:
            print(f"📝 Description: {tool_info.description}")
            print(f"🌐 Source: {tool_info.source}")
        else:
            print(f"📝 Description: {self.description}")
            print(f"🌐 Source: Unknown")
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


def create_approval_tools(tools: list, tools_manager: Any) -> list:
    """Create approval-enabled versions of tools."""
    approval_tools = []
    
    for tool in tools:
        approval_tool = ApprovalTool(tool, tools_manager)
        approval_tools.append(approval_tool)
    
    return approval_tools
