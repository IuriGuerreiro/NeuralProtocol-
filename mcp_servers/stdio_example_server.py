#!/usr/bin/env python3
"""
Example Stdio MCP Server - Basic stdio-based MCP server

This server demonstrates how to create a stdio-based MCP server
that can be used with the stdio transport.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime

# Configure logging to stderr (stdio servers should not log to stdout)
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExampleTools:
    """Collection of example tools for the stdio server."""
    
    @staticmethod
    def echo(message: str) -> str:
        """Echo back the provided message."""
        return f"Echo: {message}"
    
    @staticmethod
    def get_time() -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()
    
    @staticmethod
    def reverse(text: str) -> str:
        """Reverse the provided text."""
        return text[::-1]
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count the number of words in the provided text."""
        return len(text.split())
    
    @staticmethod
    def uppercase(text: str) -> str:
        """Convert text to uppercase."""
        return text.upper()
    
    @staticmethod
    def lowercase(text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()


class StdioMCPServer:
    """Simple stdio-based MCP server."""
    
    def __init__(self):
        self.tools = {
            "echo": {
                "name": "echo",
                "description": "Echo back the provided message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            },
            "get_time": {
                "name": "get_time",
                "description": "Get current timestamp",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "reverse": {
                "name": "reverse",
                "description": "Reverse the provided text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to reverse"
                        }
                    },
                    "required": ["text"]
                }
            },
            "count_words": {
                "name": "count_words",
                "description": "Count the number of words in the provided text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to count words in"
                        }
                    },
                    "required": ["text"]
                }
            },
            "uppercase": {
                "name": "uppercase",
                "description": "Convert text to uppercase",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to uppercase"
                        }
                    },
                    "required": ["text"]
                }
            },
            "lowercase": {
                "name": "lowercase",
                "description": "Convert text to lowercase",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to lowercase"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logger.info(f"Handling request: {method}")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "example-stdio-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": list(self.tools.values())
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found"
                        }
                    }
                
                # Get the tool method
                tool_method = getattr(ExampleTools, tool_name, None)
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
                try:
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
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Error executing tool: {str(e)}"
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
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def run(self):
        """Run the stdio server."""
        logger.info("Starting Example Stdio MCP Server...")
        
        try:
            while True:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse JSON request
                    request = json.loads(line)
                    
                    # Handle the request
                    response = await self.handle_request(request)
                    
                    # Send response to stdout
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            logger.info("Example Stdio MCP Server stopped")


async def main():
    """Main entry point."""
    server = StdioMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
