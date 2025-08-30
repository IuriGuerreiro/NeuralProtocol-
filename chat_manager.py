"""
Smart chat manager for NeuralProtocol using Gemini and Langchain.
"""

import logging
from typing import List, Optional
from datetime import datetime
import uuid

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.llms.base import LLM
from langchain_google_genai import ChatGoogleGenerativeAI

from models import ChatMessage, MessageRole, ConversationState, ChatResponse
from config import config


logger = logging.getLogger(__name__)


class SimpleLLM(LLM):
    """Simple LLM implementation for testing without API key."""
    
    def _call(self, prompt: str, stop: Optional[list] = None) -> str:
        """Generate a simple response."""
        return f"I received your message: {prompt}. This is a test response from SimpleLLM."
    
    @property
    def _llm_type(self) -> str:
        return "simple_test_llm"


class ConversationMemory:
    """Smart conversation memory with automatic summarization for NeuralProtocol."""
    
    def __init__(self, max_messages: int = 10, llm: Optional[LLM] = None):
        self.max_messages = max_messages
        self.messages: List[BaseMessage] = []
        self.llm = llm
        self.summary: Optional[str] = None
        self.summary_count = 0
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to memory, with automatic summarization when limit is reached."""
        self.messages.append(message)
        
        # Check if we need to summarize
        if len(self.messages) >= self.max_messages:
            self._summarize_conversation()
    
    def _summarize_conversation(self) -> None:
        """Create a summary of the conversation and clear old messages."""
        if not self.llm:
            # If no LLM available, just keep the last few messages
            self.messages = self.messages[-3:]  # Keep last 3 messages
            return
        
        try:
            # Create a summary prompt
            conversation_text = "\n".join([
                f"{msg.type}: {msg.content}" for msg in self.messages
            ])
            
            summary_prompt = f"""Please provide a concise summary of this conversation, capturing the key points, user preferences, and important context that should be remembered for future interactions. Focus on what's most relevant for continuing the conversation naturally.

Conversation:
{conversation_text}

Summary:"""
            
            # Generate summary using the LLM
            if hasattr(self.llm, 'invoke'):
                response = self.llm.invoke(summary_prompt)
                if hasattr(response, 'content'):
                    summary_text = response.content
                else:
                    summary_text = str(response)
            else:
                summary_text = self.llm._call(summary_prompt)
            
            # Clean up the summary
            summary_text = summary_text.strip()
            if summary_text.startswith("Summary:"):
                summary_text = summary_text[8:].strip()
            
            # Store the summary
            if self.summary:
                self.summary = f"{self.summary}\n\n{summary_text}"
            else:
                self.summary = summary_text
            
            self.summary_count += 1
            
            # Keep only the last 2 messages for immediate context
            self.messages = self.messages[-2:]
            
            logger.info(f"NeuralProtocol: Conversation summarized. Summary count: {self.summary_count}")
            
        except Exception as e:
            logger.warning(f"Failed to summarize conversation: {str(e)}")
            # Fallback: keep last few messages
            self.messages = self.messages[-3:]
    
    def get_messages(self) -> List[BaseMessage]:
        """Get all messages in memory, including summary context if available."""
        messages = []
        
        # Add summary as system message if available
        if self.summary:
            summary_msg = SystemMessage(content=f"Conversation Summary: {self.summary}")
            messages.append(summary_msg)
        
        # Add current messages
        messages.extend(self.messages)
        
        return messages
    
    def get_summary_info(self) -> dict:
        """Get information about the current summary state."""
        return {
            "has_summary": self.summary is not None,
            "summary_count": self.summary_count,
            "current_messages": len(self.messages),
            "max_messages": self.max_messages
        }
    
    def clear(self) -> None:
        """Clear all messages and summary."""
        self.messages.clear()
        self.summary = None
        self.summary_count = 0


class NeuralProtocolChatManager:
    """Manages chat conversations for NeuralProtocol using Gemini and Langchain with smart summarization."""
    
    def __init__(self):
        self.llm: Optional[LLM] = None
        self.conversations: dict[str, ConversationState] = {}
        self.memories: dict[str, ConversationMemory] = {}
        self._setup_llm()
        
    def _setup_llm(self) -> None:
        """Set up the LLM (Gemini or fallback)."""
        try:
            if config.google_api_key:
                self.llm = ChatGoogleGenerativeAI(
                    model=config.chat.model,
                    temperature=config.chat.temperature,
                    max_output_tokens=config.chat.max_tokens,
                    google_api_key=config.google_api_key
                )
                logger.info(f"NeuralProtocol: Using Gemini model: {config.chat.model}")
            else:
                self.llm = SimpleLLM()
                logger.info("NeuralProtocol: No API key found, using SimpleLLM for testing")
                
        except Exception as e:
            logger.warning(f"Failed to create Gemini LLM: {str(e)}, using SimpleLLM")
            self.llm = SimpleLLM()
    
    def create_conversation(self, conversation_id: Optional[str] = None) -> ConversationState:
        """Create a new conversation."""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        conversation = ConversationState(
            conversation_id=conversation_id,
            messages=[]
        )
        
        # Create memory for this conversation with LLM reference
        self.memories[conversation_id] = ConversationMemory(
            max_messages=config.chat.memory_size,
            llm=self.llm
        )
        
        self.conversations[conversation_id] = conversation
        logger.info(f"NeuralProtocol: Created new conversation: {conversation_id}")
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get an existing conversation."""
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, message: ChatMessage) -> None:
        """Add a message to a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            conversation = self.create_conversation(conversation_id)
        
        conversation.add_message(message)
        
        # Also add to memory (this will trigger summarization if needed)
        if conversation_id in self.memories:
            if message.role == MessageRole.USER:
                self.memories[conversation_id].add_message(HumanMessage(content=message.content))
            elif message.role == MessageRole.ASSISTANT:
                self.memories[conversation_id].add_message(AIMessage(content=message.content))
            elif message.role == MessageRole.SYSTEM:
                self.memories[conversation_id].add_message(SystemMessage(content=message.content))
    
    def generate_response(self, conversation_id: str, user_input: str) -> ChatResponse:
        """Generate a response using Gemini/Langchain."""
        if not self.llm:
            raise ValueError("LLM not initialized")
        
        start_time = datetime.utcnow()
        
        try:
            # Add user message to conversation
            user_message = ChatMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.USER,
                content=user_input
            )
            self.add_message(conversation_id, user_message)
            
            # Get conversation context from memory (includes summary if available)
            memory = self.memories.get(conversation_id)
            context_messages = memory.get_messages() if memory else []
            
            # Check if summarization just happened
            summary_info = memory.get_summary_info() if memory else {}
            if summary_info.get("has_summary") and summary_info.get("summary_count", 0) > 0:
                # Add a note about the summary
                summary_note = f"\n[Note: Previous conversation has been summarized to maintain context]"
                user_input_with_note = user_input + summary_note
            
            # Generate response using the LLM
            if hasattr(self.llm, 'invoke'):
                # For newer LLM implementations
                if context_messages:
                    # Use conversation context (includes summary)
                    response = self.llm.invoke(context_messages)
                else:
                    # Direct input
                    response = self.llm.invoke(user_input)
                
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
            else:
                # Fallback for older LLM implementations
                if context_messages:
                    # Build context string
                    context_str = "\n".join([f"{msg.type}: {msg.content}" for msg in context_messages])
                    full_input = f"Context:\n{context_str}\n\nUser: {user_input}"
                    response_text = self.llm._call(full_input)
                else:
                    response_text = self.llm._call(user_input)
            
            # Create AI message
            ai_message = ChatMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=response_text
            )
            self.add_message(conversation_id, ai_message)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create response
            response_obj = ChatResponse(
                message=ai_message,
                processing_time=processing_time
            )
            
            logger.info(f"NeuralProtocol: Generated response in {processing_time:.2f}s")
            return response_obj
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            error_message = ChatMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=f"Sorry, I encountered an error: {str(e)}"
            )
            
            return ChatResponse(
                message=error_message,
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def get_conversation_history(self, conversation_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get conversation history."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = conversation.messages
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_memory_info(self, conversation_id: str) -> dict:
        """Get information about the conversation memory state."""
        memory = self.memories.get(conversation_id)
        if memory:
            return memory.get_summary_info()
        return {}
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation's history."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.messages.clear()
            conversation.updated_at = datetime.utcnow()
            
            # Clear memory
            if conversation_id in self.memories:
                self.memories[conversation_id].clear()
            
            logger.info(f"NeuralProtocol: Cleared conversation: {conversation_id}")
            return True
        
        return False
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs."""
        return list(self.conversations.keys())
