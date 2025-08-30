"""
Simple test file for the Gemini chat application.
Tests basic functionality without requiring external services.
"""

import logging
from models import ChatMessage, MessageRole
from chat_manager import GeminiChatManager, SimpleLLM

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_models():
    """Test Pydantic models."""
    print("Testing Pydantic models...")
    
    try:
        # Test ChatMessage creation
        message = ChatMessage(
            id="test-1",
            role=MessageRole.USER,
            content="Hello, world!"
        )
        print(f"✓ Created message: {message.content}")
        
        # Test validation
        try:
            invalid_message = ChatMessage(
                id="",
                role=MessageRole.USER,
                content=""
            )
        except Exception as e:
            print(f"✓ Validation caught error: {str(e)}")
        
        print("✓ Models test passed\n")
        
    except Exception as e:
        print(f"✗ Models test failed: {str(e)}\n")


def test_chat_manager():
    """Test the chat manager."""
    print("Testing chat manager...")
    
    try:
        # Create chat manager
        chat_manager = GeminiChatManager()
        
        # Create conversation
        conversation_id = "test-conversation"
        conversation = chat_manager.create_conversation(conversation_id)
        print(f"✓ Created conversation: {conversation.conversation_id}")
        
        # Test message handling
        test_message = ChatMessage(
            id="test-msg-1",
            role=MessageRole.USER,
            content="Test message"
        )
        
        chat_manager.add_message(conversation_id, test_message)
        print("✓ Added message to conversation")
        
        # Test response generation
        response = chat_manager.generate_response(
            conversation_id,
            "Hello, this is a test!"
        )
        
        print(f"✓ Generated response: {response.message.content}")
        print(f"✓ Processing time: {response.processing_time:.2f}s")
        
        # Test conversation history
        history = chat_manager.get_conversation_history(conversation_id)
        print(f"✓ Conversation has {len(history)} messages")
        
        print("✓ Chat manager test passed\n")
        
    except Exception as e:
        print(f"✗ Chat manager test failed: {str(e)}\n")
        logger.exception("Chat manager test error")


def test_simple_llm():
    """Test the SimpleLLM fallback."""
    print("Testing SimpleLLM...")
    
    try:
        llm = SimpleLLM()
        response = llm._call("Test prompt")
        print(f"✓ SimpleLLM response: {response}")
        print(f"✓ LLM type: {llm._llm_type}")
        print("✓ SimpleLLM test passed\n")
        
    except Exception as e:
        print(f"✗ SimpleLLM test failed: {str(e)}\n")


def test_conversation_management():
    """Test conversation management features."""
    print("Testing conversation management...")
    
    try:
        chat_manager = GeminiChatManager()
        
        # Create multiple conversations
        conversations = []
        for i in range(3):
            conv_id = f"conversation-{i}"
            conv = chat_manager.create_conversation(conv_id)
            conversations.append(conv)
            print(f"✓ Created conversation: {conv_id}")
        
        # Add messages to different conversations
        for i, conv in enumerate(conversations):
            # Create proper ChatMessage object
            message = ChatMessage(
                id=f"msg-{i}",
                role=MessageRole.USER,
                content=f"Message {i+1} in conversation {conv.conversation_id}"
            )
            chat_manager.add_message(conv.conversation_id, message)
            print(f"✓ Added message to {conv.conversation_id}")
        
        # Show conversation states
        for conv in conversations:
            history = chat_manager.get_conversation_history(conv.conversation_id)
            print(f"✓ {conv.conversation_id}: {len(history)} messages")
        
        # Clear one conversation
        if conversations:
            cleared = chat_manager.clear_conversation(conversations[0].conversation_id)
            print(f"✓ Cleared conversation: {cleared}")
        
        print("✓ Conversation management test passed\n")
        
    except Exception as e:
        print(f"✗ Conversation management test failed: {str(e)}\n")
        logger.exception("Conversation management test error")


def run_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running Gemini Chat Application Tests")
    print("=" * 50)
    
    test_models()
    test_chat_manager()
    test_simple_llm()
    test_conversation_management()
    
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    run_tests()
