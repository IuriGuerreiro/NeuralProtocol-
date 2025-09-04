"""
Enhanced NeuralProtocol Langchain Chat with Database Integration

Enhanced version of the original langchain_chat.py that integrates with Django models
for persistent data storage while maintaining all original functionality.
"""

import asyncio
import logging
import os
from typing import List, Optional, Dict
from datetime import datetime
import time
import uuid

import google.generativeai as genai
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from django.contrib.auth import get_user_model

from .utils.mcp_studio import MCPStudio, Configuration
from .utils.tools_manager import ToolsManager
from .utils.custom_tools import get_all_custom_tools
from .utils.mcp_see_http import HttpMCPStudio, get_supported_transports
from .models import ChatSession, Message, ToolExecution
from .database_service import chat_db

User = get_user_model()

# Configure logging with more readable format
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)


class EnhancedMessage(BaseModel):
    """Enhanced Pydantic model for validating chat messages with database integration."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Timestamp of the message")
    tokens_used: Optional[int] = Field(default=0, description="Number of tokens used")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    model_used: Optional[str] = Field(None, description="Model used for generation")
    tools_used: Optional[List[str]] = Field(default_factory=list, description="Tools used in this message")


class EnhancedChatHistory(BaseModel):
    """Enhanced Pydantic model for managing chat history with database sync."""
    messages: List[EnhancedMessage] = Field(default_factory=list, description="List of chat messages")
    session_id: Optional[str] = Field(None, description="Unique session identifier")
    db_session: Optional[ChatSession] = Field(None, description="Django model instance")


class EnhancedNeuralProtocolChat:
    """Enhanced main chat application class with database integration."""
    
    def __init__(self, session: Optional[ChatSession] = None, config_file: str = "servers_config.json"):
        self.config = Configuration()
        self.mcp_studio = MCPStudio(self.config)
        self.http_mcp_studio = HttpMCPStudio()
        self.tools_manager = ToolsManager(self.mcp_studio, self.http_mcp_studio)
        self.chat_history = EnhancedChatHistory()
        self.llm = None
        self.agent = None
        self.config_file = config_file
        
        # Database integration
        self.db_session = session
        if session:
            self.chat_history.session_id = str(session.session_id)
            self.chat_history.db_session = session
            self._load_messages_from_db()
        else:
            # Generate temporary session ID for non-persistent mode
            self.chat_history.session_id = f"temp_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _load_messages_from_db(self):
        """Load existing messages from database"""
        if not self.db_session:
            return
            
        db_messages = chat_db.get_session_messages(self.db_session)
        self.chat_history.messages = []
        
        for db_msg in db_messages:
            enhanced_msg = EnhancedMessage(
                role=db_msg.role,
                content=db_msg.content,
                timestamp=db_msg.timestamp,
                tokens_used=db_msg.tokens_used,
                processing_time=db_msg.processing_time,
                model_used=db_msg.model_used,
                tools_used=db_msg.tools_used
            )
            self.chat_history.messages.append(enhanced_msg)
    
    def _save_message_to_db(self, message: EnhancedMessage) -> Optional[Message]:
        """Save a message to the database"""
        if not self.db_session:
            return None
            
        return chat_db.save_message(
            session=self.db_session,
            role=message.role,
            content=message.content,
            tokens_used=message.tokens_used,
            processing_time=message.processing_time,
            model_used=message.model_used,
            tools_used=message.tools_used,
            tool_results={},
            metadata={}
        )
    
    async def initialize_llm(self, model_name: str = "gemini-2.0-flash", provider: str = "google_genai") -> None:
        """Initialize the LLM using Langchain's init_chat_model."""
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
    
    async def process_message(self, user_input: str) -> str:
        """Process a user message and return the agent's response with database persistence."""
        try:
            start_time = time.time()
            
            # Create and validate user message
            user_message = EnhancedMessage(role="user", content=user_input)
            self.chat_history.messages.append(user_message)
            
            # Save user message to database
            self._save_message_to_db(user_message)

            # Get response from agent
            if not self.agent:
                raise RuntimeError("Agent not initialized")

            # Prepare messages for the agent
            agent_messages = [{"role": msg.role, "content": msg.content} for msg in self.chat_history.messages]
            
            # Process with or without approval
            if self.tools_manager.approval_enabled:
                response = await self._process_with_approval(agent_messages)
            else:
                response = await self.agent.ainvoke({"messages": agent_messages})
            
            # Extract the response content
            if isinstance(response, dict) and "messages" in response:
                assistant_content = response["messages"][-1].content if response["messages"] else "No response"
            else:
                assistant_content = str(response)

            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create and validate assistant message
            assistant_message = EnhancedMessage(
                role="assistant", 
                content=assistant_content,
                processing_time=processing_time,
                model_used=self.db_session.model_name if self.db_session else "unknown"
            )
            self.chat_history.messages.append(assistant_message)
            
            # Save assistant message to database
            self._save_message_to_db(assistant_message)
            
            # Update session activity
            if self.db_session:
                chat_db.update_session_activity(self.db_session)

            return assistant_content

        except Exception as e:
            error_message = f"❌ Error processing message: {e}"
            logging.error(error_message)
            return error_message
    
    async def _process_with_approval(self, agent_messages: List[Dict[str, str]]) -> str:
        """Process agent messages with tool approval system."""
        # For now, just run the agent normally
        # In a real implementation, this would handle the approval workflow
        return await self.agent.ainvoke({"messages": agent_messages})
    
    def add_system_message(self, content: str = None) -> None:
        """Add a system message to the conversation."""
        if not content:
            content = "You are a helpful AI assistant with access to various tools. Use them to help answer user questions."
        
        system_message = EnhancedMessage(role="system", content=content)
        self.chat_history.messages.append(system_message)
        
        # Save to database
        self._save_message_to_db(system_message)
    
    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.chat_history.messages)
    
    def clear_history(self) -> None:
        """Clear chat history but keep system message."""
        if self.db_session:
            chat_db.clear_session_messages(self.db_session)
        
        # Clear in-memory history
        self.chat_history.messages = []
        
        # Re-add system message
        self.add_system_message()
    
    def get_statistics(self) -> Dict:
        """Get session statistics."""
        if self.db_session:
            return chat_db.get_session_statistics(self.db_session)
        else:
            # Return basic stats for non-persistent sessions
            messages = self.chat_history.messages
            return {
                'total_messages': len(messages),
                'user_messages': len([m for m in messages if m.role == 'user']),
                'assistant_messages': len([m for m in messages if m.role == 'assistant']),
                'system_messages': len([m for m in messages if m.role == 'system']),
                'total_tokens': sum(m.tokens_used for m in messages),
                'session_duration': None,
                'last_activity': datetime.now(),
                'approval_mode': self.tools_manager.approval_enabled
            }
    
    async def initialize_all(self, model_name: str = None, provider: str = None) -> None:
        """Initialize all components in the correct order."""
        try:
            logging.info("🚀 Initializing Enhanced NeuralProtocol Chat...")
            
            # Use session settings if available
            if self.db_session:
                model_name = model_name or self.db_session.model_name
                provider = provider or self.db_session.provider
            
            # Initialize everything step by step
            await self.initialize_llm(
                model_name or "gemini-2.0-flash",
                provider or "google_genai"
            )
            await self.initialize_mcp_servers()
            await self.initialize_tools()
            await self.create_agent()

            logging.info("✅ All components initialized successfully!")
            
            # Add system message if no messages exist
            if not self.chat_history.messages:
                self.add_system_message()
                
        except Exception as e:
            logging.error(f"❌ Error initializing Enhanced NeuralProtocol Chat: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            await self.mcp_studio.cleanup_all_servers()
            await self.http_mcp_studio.cleanup_all_servers()
            logging.info("🧹 Cleanup completed")
        except Exception as e:
            logging.error(f"❌ Error during cleanup: {e}")


# Factory function for creating enhanced chat instances
def create_enhanced_chat(session: Optional[ChatSession] = None, config_file: str = "servers_config.json") -> EnhancedNeuralProtocolChat:
    """Factory function to create enhanced chat instances."""
    return EnhancedNeuralProtocolChat(session=session, config_file=config_file)