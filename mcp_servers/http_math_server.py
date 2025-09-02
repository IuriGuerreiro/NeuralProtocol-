"""
HTTP Math Server - Simple HTTP-based MCP server for math operations

This server provides basic math operations via HTTP endpoints.
It can be used to test HTTP/SSE transport functionality.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HTTP Math Server",
    description="Simple HTTP-based MCP server for math operations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ToolCallRequest(BaseModel):
    """Request model for tool calls."""
    tool: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(..., description="Arguments for the tool")
    timestamp: Optional[str] = Field(None, description="Timestamp of the request")


class ToolResponse(BaseModel):
    """Response model for tool calls."""
    success: bool = Field(..., description="Whether the operation was successful")
    result: Any = Field(..., description="Result of the operation")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MathTools:
    """Collection of math tools."""
    
    @staticmethod
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    @staticmethod
    def subtract(a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b
    
    @staticmethod
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    @staticmethod
    def divide(a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    @staticmethod
    def power(a: float, b: float) -> float:
        """Raise a to the power of b."""
        return a ** b
    
    @staticmethod
    def sqrt(a: float) -> float:
        """Calculate square root of a."""
        if a < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return a ** 0.5
    
    @staticmethod
    def factorial(n: int) -> int:
        """Calculate factorial of n."""
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result


# Available tools
TOOLS = {
    "add": {
        "name": "add",
        "description": "Add two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    "subtract": {
        "name": "subtract",
        "description": "Subtract b from a",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    "multiply": {
        "name": "multiply",
        "description": "Multiply two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    "divide": {
        "name": "divide",
        "description": "Divide a by b",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    "power": {
        "name": "power",
        "description": "Raise a to the power of b",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "Base number"},
                "b": {"type": "number", "description": "Exponent"}
            },
            "required": ["a", "b"]
        }
    },
    "sqrt": {
        "name": "sqrt",
        "description": "Calculate square root of a number",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "Number to calculate square root of"}
            },
            "required": ["a"]
        }
    },
    "factorial": {
        "name": "factorial",
        "description": "Calculate factorial of a number",
        "parameters": {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "Number to calculate factorial of"}
            },
            "required": ["n"]
        }
    }
}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HTTP Math Server",
        "version": "1.0.0",
        "tools": list(TOOLS.keys()),
        "endpoints": {
            "tools": "/tools",
            "tool_call": "/tools/{tool_name}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/tools")
async def list_tools():
    """List all available tools."""
    return {"tools": list(TOOLS.values())}


@app.get("/api/tools")
async def list_tools_api():
    """Alternative endpoint to list tools."""
    return {"tools": list(TOOLS.values())}


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: ToolCallRequest):
    """Call a specific tool."""
    try:
        if tool_name not in TOOLS:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Get the tool method
        tool_method = getattr(MathTools, tool_name, None)
        if not tool_method:
            raise HTTPException(status_code=500, detail=f"Tool method '{tool_name}' not implemented")
        
        # Execute the tool
        logger.info(f"Executing tool '{tool_name}' with arguments: {request.arguments}")
        result = tool_method(**request.arguments)
        
        return ToolResponse(
            success=True,
            result=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}")
        return ToolResponse(
            success=False,
            result=None,
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/api/tools/{tool_name}")
async def call_tool_api(tool_name: str, request: ToolCallRequest):
    """Alternative endpoint to call a tool."""
    return await call_tool(tool_name, request)


@app.post("/mcp/tools/{tool_name}")
async def call_tool_mcp(tool_name: str, request: ToolCallRequest):
    """MCP protocol endpoint to call a tool."""
    return await call_tool(tool_name, request)


@app.get("/mcp/tools")
async def list_tools_mcp():
    """MCP protocol endpoint to list tools."""
    return {"tools": list(TOOLS.values())}


@app.post("/mcp")
async def mcp_protocol(request: Dict[str, Any]):
    """Handle MCP protocol requests."""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id", 1)
        
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": list(TOOLS.values())
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in TOOLS:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    }
                }
            
            # Get the tool method
            tool_method = getattr(MathTools, tool_name, None)
            if not tool_method:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Tool method '{tool_name}' not implemented"
                    }
                }
            
            # Execute the tool
            logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
            result = tool_method(**arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }
            
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


if __name__ == "__main__":
    logger.info("Starting HTTP Math Server...")
    uvicorn.run(
        "http_math_server:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
