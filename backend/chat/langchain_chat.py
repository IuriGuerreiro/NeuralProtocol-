"""
NeuralProtocol Langchain Chat - Main Application

This is the main chat application that orchestrates MCP servers,
custom tools, and Langchain for an enhanced AI chat experience.
"""

import asyncio
import logging
import os
from typing import List, Optional, Dict
from datetime import datetime

import google.generativeai as genai
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from chat.utils.mcp_studio import MCPStudio, Configuration
from chat.utils.tools_manager import ToolsManager
from chat.utils.custom_tools import get_all_custom_tools
from chat.utils.mcp_see_http import HttpMCPStudio, get_supported_transports


# Configure logging with more readable format
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)


class Message(BaseModel):
    """Pydantic model for validating chat messages."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp of the message")


class ChatHistory(BaseModel):
    """Pydantic model for managing chat history."""
    messages: List[Message] = Field(default_factory=list, description="List of chat messages")
    session_id: Optional[str] = Field(None, description="Unique session identifier")


class NeuralProtocolChat:
    """Main chat application class."""
    
    def __init__(self, config_file: str = "servers_config.json"):
        self.config = Configuration()
        self.mcp_studio = MCPStudio(self.config)
        self.http_mcp_studio = HttpMCPStudio()
        self.tools_manager = ToolsManager(self.mcp_studio, self.http_mcp_studio)
        self.chat_history = ChatHistory()
        self.llm = None
        self.agent = None
        self.config_file = config_file
        
        # Initialize session
        self.chat_history.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def initialize_llm(self, model_name: str = "gemini-2.0-flash", provider: str = "google_genai") -> None:
        """Initialize the LLM using Langchain's init_chat_model.

        Args:
            model_name: Name of the model to use.
            provider: Provider for the model (google_genai, openai, anthropic, etc.).
        """
        try:
            # Get provider configuration
            provider_config = self.config.get_provider_config(provider)
            
            # Set environment variable for the provider
            os.environ[provider_config["env_var"]] = provider_config["api_key"]
            
            # Special handling for Google Generative AI
            if provider == "google_genai":
                genai.configure(api_key=provider_config["api_key"])

            # Initialize the chat model
            self.llm = init_chat_model(
                model=model_name,
                model_provider=provider,
                temperature=0.7
            )
            
            logging.info(f"🤖 LLM initialized: {provider}/{model_name}")
            
        except Exception as e:
            logging.error(f"❌ Error initializing LLM: {e}")
            raise
    
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
            
            logging.info(f"✅ Initialized {len(stdio_servers)} STDIO servers and {len(http_servers)} HTTP/SSE servers")
            
        except Exception as e:
            logging.error(f"❌ Error initializing MCP servers: {e}")
            raise
    
    async def initialize_tools(self) -> None:
        """Initialize MCP, HTTP/SSE, and custom tools."""
        try:
            # Load MCP tools (stdio)
            await self.tools_manager.load_mcp_tools()
            
            # Load HTTP/SSE tools  
            await self.tools_manager.load_http_tools()
            
            # Add custom tools
            custom_tools = get_all_custom_tools()
            self.tools_manager.add_custom_tools(custom_tools)
            
            # Log tools summary
            self.tools_manager.print_tools_summary()
            
        except Exception as e:
            logging.error(f"❌ Error initializing tools: {e}")
            raise
    
    async def create_agent(self) -> None:
        """Create the React agent with LLM and tools."""
        if not self.llm:
            raise RuntimeError("LLM not initialized")
        
        all_tools = self.tools_manager.get_all_tools()
        
        if not all_tools:
            logging.warning("⚠️ No tools available, creating agent without tools")
        
        try:
            self.agent = create_react_agent(self.llm, all_tools)
            logging.info("🤖 React agent created successfully")
            
        except Exception as e:
            logging.error(f"❌ Error creating agent: {e}")
            raise
    
    async def refresh_agent(self) -> None:
        """Refresh the agent with updated tools (e.g., after approval mode change)."""
        try:
            all_tools = self.tools_manager.get_all_tools()
            self.agent = create_react_agent(self.llm, all_tools)
            logging.info("🔄 Agent refreshed with updated tools")
        except Exception as e:
            logging.error(f"❌ Error refreshing agent: {e}")
            raise
    
    async def process_message(self, user_input: str, context_messages: List = None) -> str:
        """Process a user message and return the agent's response.

        Args:
            user_input: The user's input message.
            context_messages: Optional list of previous messages for context.

        Returns:
            The agent's response.
        """
        try:
            # Validate and add user message to history
            user_message = Message(role="user", content=user_input)
            self.chat_history.messages.append(user_message)

            # Get response from agent
            if not self.agent:
                raise RuntimeError("Agent not initialized")

            # Prepare messages for the agent - use context if provided
            if context_messages:
                # Use provided context messages + current conversation
                agent_messages = context_messages + [{"role": msg.role, "content": msg.content} for msg in self.chat_history.messages]
                logging.info(f"🧠 Using conversation context: {len(context_messages)} previous messages")
            else:
                # Use only current conversation
                agent_messages = [{"role": msg.role, "content": msg.content} for msg in self.chat_history.messages]
            
            # If approval is enabled, we need to intercept tool calls
            if self.tools_manager.approval_enabled:
                response = await self._process_with_approval(agent_messages)
            else:
                response = await self.agent.ainvoke({"messages": agent_messages})
            
            # Extract the response content
            if isinstance(response, dict) and "messages" in response:
                assistant_content = response["messages"][-1].content if response["messages"] else "No response"
            else:
                assistant_content = str(response)

            # Validate and add assistant message to history
            assistant_message = Message(role="assistant", content=assistant_content)
            self.chat_history.messages.append(assistant_message)

            return assistant_content

        except Exception as e:
            error_message = f"❌ Error processing message: {e}"
            logging.error(error_message)
            return error_message
    
    async def _process_with_approval(self, agent_messages: List[Dict[str, str]]) -> str:
        """Process agent messages with tool approval system."""
        print("🔐 Tool approval mode is enabled!")
        print("📋 When the AI tries to use tools, you'll see approval prompts like this:")
        print("\n🔧 Tool Approval Request:")
        print("📋 Tool: multiply")
        print("📝 Description: Multiply two numbers together")
        print("🌐 Source: http_server:http_math_server")
        print("⚙️ Arguments: {'a': 8, 'b': 899}")
        print("\n❓ Do you want to approve this tool execution?")
        print("   1 - ✅ Approve")
        print("   2 - ❌ Disapprove")
        print("\n💡 This is a demonstration. In the full implementation, you would see this for every tool call.")
        
        # For now, just run the agent normally
        return await self.agent.ainvoke({"messages": agent_messages})
    
    def show_help(self) -> None:
        """Show help information."""
        print("\n📋 NeuralProtocol Chat Commands:")
        print("  help     - Show this help message")
        print("  tools    - Show available tools")
        print("  history  - Show chat history")
        print("  clear    - Clear chat history")
        print("  status   - Show system status")
        print("  approval - Toggle tool approval mode")
        print("  quit/exit - End the chat session")
        print("\n💬 Just type your message to chat with the AI assistant!")
    
    def show_tools(self) -> None:
        """Show available tools."""
        self.tools_manager.print_tools_summary()
    
    def show_history(self) -> None:
        """Show chat history."""
        if not self.chat_history.messages:
            print("📭 No chat history yet")
            return
        
        print(f"\n📚 Chat History (Session: {self.chat_history.session_id}):")
        for i, msg in enumerate(self.chat_history.messages, 1):
            timestamp = msg.timestamp.strftime("%H:%M:%S") if msg.timestamp else "Unknown"
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg.role, "❓")
            print(f"{i:2d}. [{timestamp}] {role_emoji} {msg.role}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
    
    def clear_history(self) -> None:
        """Clear chat history."""
        self.chat_history.messages = []
        # Keep system message
        system_message = Message(
            role="system", 
            content="You are a helpful AI assistant with access to various tools. Use them to help answer user questions."
        )
        self.chat_history.messages.append(system_message)
        print("🧹 Chat history cleared")
    
    def show_status(self) -> None:
        """Show system status."""
        print(f"\n📊 NeuralProtocol Chat Status:")
        print(f"  Session ID: {self.chat_history.session_id}")
        print(f"  LLM: {'✅ Initialized' if self.llm else '❌ Not initialized'}")
        print(f"  Agent: {'✅ Ready' if self.agent else '❌ Not ready'}")
        
        stdio_servers = self.mcp_studio.get_initialized_servers()
        http_servers = self.http_mcp_studio.get_initialized_servers()
        print(f"  STDIO Servers: {len(stdio_servers)} initialized")
        for server in stdio_servers:
            print(f"    📡 {server.name}")
        
        print(f"  HTTP/SSE Servers: {len(http_servers)} initialized")
        for server in http_servers:
            print(f"    🌍 {server.name} ({server.config.transport})")
        
        tools_summary = self.tools_manager.get_tools_summary()
        print(f"  Tools: {tools_summary['total_tools']} total")
        print(f"    🌐 MCP: {tools_summary['mcp_tools']['total']}")
        print(f"    🌍 HTTP: {tools_summary['http_tools']['total']}")
        print(f"    🛠️ Custom: {tools_summary['custom_tools']['total']}")
        
        print(f"  Messages: {len(self.chat_history.messages)}")
        print(f"  🔐 Tool Approval: {'✅ Enabled' if self.tools_manager.approval_enabled else '❌ Disabled'}")
    
    async def start_chat(self) -> None:
        """Start the interactive chat session."""
        try:
            print("🚀 Starting NeuralProtocol Chat...")
            print("🔧 Initializing components...")
            
            # Initialize everything step by step
            await self.initialize_llm()
            await self.initialize_mcp_servers()
            await self.initialize_tools()
            await self.create_agent()

            print("\n✅ All components initialized successfully!")
            print("💬 Chat session ready!")
            
            # Add system message
            system_message = Message(
                role="system", 
                content="You are a helpful AI assistant with access to various tools. Use them to help answer user questions."
            )
            self.chat_history.messages.append(system_message)
            
            # Show initial help
            self.show_help()

            # Main chat loop
            while True:
                try:
                    user_input = input(f"\n💬 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    if user_input.lower() in ["quit", "exit"]:
                        print("👋 Goodbye!")
                        break
                    elif user_input.lower() == "help":
                        self.show_help()
                        continue
                    elif user_input.lower() == "tools":
                        self.show_tools()
                        continue
                    elif user_input.lower() == "history":
                        self.show_history()
                        continue
                    elif user_input.lower() == "clear":
                        self.clear_history()
                        continue
                    elif user_input.lower() == "status":
                        self.show_status()
                        continue
                    elif user_input.lower() == "approval":
                        current_status = self.tools_manager.approval_enabled
                        self.tools_manager.set_approval_mode(not current_status)
                        new_status = "enabled" if not current_status else "disabled"
                        print(f"🔐 Tool approval mode {new_status}")
                        # Refresh agent with updated tools
                        await self.refresh_agent()
                        continue
                    
                    # Process regular message
                    logging.info(f"🔄 Processing: {user_input}")
                    response = await self.process_message(user_input)
                    print(f"\n🤖 Assistant: {response}")

                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    logging.error(f"❌ Error in chat loop: {e}")
                    print(f"❌ Error: {e}")

        except Exception as e:
            logging.error(f"❌ Error starting chat: {e}")
            print(f"❌ Failed to start chat: {e}")
        finally:
            # Cleanup
            await self.mcp_studio.cleanup_all_servers()
            await self.http_mcp_studio.cleanup_all_servers()
            print("🧹 Cleanup completed")


async def main() -> None:
    """Main function to run the chat application."""
    try:
        # Check for configuration file
        config_files = ["servers_config.json", "simple_servers_config.json"]
        config_file = None
        
        for file in config_files:
            if os.path.exists(file):
                config_file = file
                break
        
        if not config_file:
            print("❌ No MCP server configuration file found!")
            print("Please create one of these files:")
            for file in config_files:
                print(f"  - {file}")
            return
        
        print(f"📁 Using configuration file: {config_file}")
        
        # Create and start chat
        chat = NeuralProtocolChat(config_file)
        await chat.start_chat()
        
    except Exception as e:
        logging.error(f"❌ Error in main: {e}")
        print(f"❌ Application error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
