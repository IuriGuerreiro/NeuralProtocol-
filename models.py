"""
Simple Pydantic models for the Gemini chat application.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in the conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual chat message."""
    id: str = Field(description="Unique message identifier")
    role: MessageRole = Field(description="Role of the message sender")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    @validator('id')
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message ID cannot be empty')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message content cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Response from the chat system."""
    message: ChatMessage = Field(description="The response message")
    processing_time: Optional[float] = Field(default=None, description="Processing time in seconds")
    tokens_used: Optional[int] = Field(default=None, description="Number of tokens used")


class ConversationState(BaseModel):
    """State of the current conversation."""
    conversation_id: str = Field(description="Unique conversation identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="List of messages")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    @validator('conversation_id')
    def validate_conversation_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Conversation ID cannot be empty')
        return v.strip()
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """Get the most recent messages."""
        return self.messages[-count:] if len(self.messages) > count else self.messages
