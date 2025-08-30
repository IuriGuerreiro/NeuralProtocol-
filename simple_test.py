"""
Simple test script to demonstrate the chat functionality.
"""

from chat_manager import GeminiChatManager
from models import ChatMessage, MessageRole

def test_simple_chat():
    """Test a simple chat conversation."""
    print("=== Simple Chat Test ===")
    
    # Create chat manager
    chat_manager = GeminiChatManager()
    
    # Create a conversation
    conversation_id = "demo-conversation"
    conversation = chat_manager.create_conversation(conversation_id)
    print(f"Created conversation: {conversation_id}")
    
    # Test messages
    test_messages = [
        "Hello! How are you today?",
        "What's the weather like?",
        "Can you tell me a joke?",
        "What's 2 + 2?"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n--- Message {i+1} ---")
        print(f"You: {message}")
        
        # Generate response
        response = chat_manager.generate_response(conversation_id, message)
        print(f"Assistant: {response.message.content}")
        print(f"Processing time: {response.processing_time:.3f}s")
    
    # Show conversation history
    print(f"\n--- Conversation Summary ---")
    history = chat_manager.get_conversation_history(conversation_id)
    print(f"Total messages: {len(history)}")
    
    # Show recent messages
    print("\nRecent messages:")
    for msg in history[-6:]:  # Last 6 messages
        role = msg.role.value.capitalize()
        print(f"  {role}: {msg.content[:50]}{'...' if len(msg.content) > 50 else ''}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_simple_chat()

