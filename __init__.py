"""
NeuralProtocol - AI-Powered MCP Chat Platform

A sophisticated AI chat application built with Langchain, Pydantic, and Gemini 2.0 Flash.
Features intelligent conversation management with automatic summarization.
"""

__version__ = "1.0.0"
__author__ = "NeuralProtocol Team"
__description__ = "AI-Powered MCP Chat Platform with Smart Memory Management"

# Import main classes
from .chat_manager import NeuralProtocolChatManager, ConversationMemory, SimpleLLM
from .models import ChatMessage, MessageRole, ConversationState, ChatResponse
from .config import Config

__all__ = [
    "NeuralProtocolChatManager",
    "ConversationMemory", 
    "SimpleLLM",
    "ChatMessage",
    "MessageRole",
    "ConversationState",
    "ChatResponse",
    "Config"
]
