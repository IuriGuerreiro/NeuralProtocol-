"""
Main application for NeuralProtocol - AI-Powered MCP Chat Platform.
"""

import logging
from datetime import datetime
from typing import Optional

from chat_manager import NeuralProtocolChatManager
from models import ChatMessage, MessageRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NeuralProtocolApp:
    """Main chat application class for NeuralProtocol."""
    
    def __init__(self):
        self.chat_manager = NeuralProtocolChatManager()
        self.current_conversation_id: Optional[str] = None
    
    def initialize(self) -> None:
        """Initialize the NeuralProtocol application."""
        logger.info("Initializing NeuralProtocol - AI-Powered MCP Chat Platform...")
        
        # Create initial conversation
        conversation = self.chat_manager.create_conversation()
        self.current_conversation_id = conversation.conversation_id
        
        logger.info("NeuralProtocol application initialized successfully")
    
    def send_message(self, message: str) -> str:
        """Send a message and get response."""
        if not self.current_conversation_id:
            raise ValueError("No active conversation")
        
        response = self.chat_manager.generate_response(
            self.current_conversation_id, 
            message
        )
        return response.message.content
    
    def get_conversation_history(self, limit: Optional[int] = None) -> list:
        """Get conversation history."""
        if not self.current_conversation_id:
            return []
        
        return self.chat_manager.get_conversation_history(
            self.current_conversation_id, 
            limit
        )
    
    def clear_conversation(self) -> bool:
        """Clear current conversation."""
        if not self.current_conversation_id:
            return False
        
        return self.chat_manager.clear_conversation(self.current_conversation_id)
    
    def show_status(self) -> None:
        """Show application status."""
        print("\n--- NeuralProtocol Status ---")
        print(f"Model: {self.chat_manager.llm._llm_type if self.chat_manager.llm else 'Unknown'}")
        print(f"Temperature: {self.chat_manager.llm.temperature if hasattr(self.chat_manager.llm, 'temperature') else 'N/A'}")
        print(f"Max Tokens: {self.chat_manager.llm.max_output_tokens if hasattr(self.chat_manager.llm, 'max_output_tokens') else 'N/A'}")
        print(f"Memory Size: {self.chat_manager.llm._llm_type if self.chat_manager.llm else 'Unknown'}")
        print(f"API Key: {'✓ Set' if hasattr(self.chat_manager.llm, 'google_api_key') else '✗ Not Set'}")
        print(f"Conversation ID: {self.current_conversation_id}")
        
        # Show memory status
        if self.current_conversation_id:
            memory_info = self.chat_manager.get_memory_info(self.current_conversation_id)
            if memory_info:
                print(f"Memory Status: {memory_info['current_messages']}/{memory_info['max_messages']} messages")
                if memory_info.get('has_summary'):
                    print(f"Summaries: {memory_info['summary_count']} created")
                    print(f"Context: Summary + {memory_info['current_messages']} recent messages")
        
        print("------------------------------")
    
    def show_memory_info(self) -> None:
        """Show detailed memory information."""
        if not self.current_conversation_id:
            print("No active conversation.")
            return
        
        memory_info = self.chat_manager.get_memory_info(self.current_conversation_id)
        if not memory_info:
            print("No memory information available.")
            return
        
        print("\n--- Memory Status ---")
        print(f"Current Messages: {memory_info['current_messages']}")
        print(f"Max Messages: {memory_info['max_messages']}")
        print(f"Has Summary: {'Yes' if memory_info['has_summary'] else 'No'}")
        print(f"Summary Count: {memory_info['summary_count']}")
        
        if memory_info['has_summary']:
            memory = self.chat_manager.memories.get(self.current_conversation_id)
            if memory and memory.summary:
                print(f"\nCurrent Summary:")
                print(f"{memory.summary[:200]}{'...' if len(memory.summary) > 200 else ''}")
        
        print("------------------------------")


def interactive_chat(app: NeuralProtocolApp) -> None:
    """Interactive chat loop for NeuralProtocol."""
    print("\n=== NeuralProtocol - AI-Powered MCP Chat Platform ===")
    print("Type 'quit' to exit, 'clear' to clear conversation, 'history' to show history")
    print("Type 'status' to show application status, 'memory' to show memory info")
    print("==================================================\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye from NeuralProtocol!")
                break
            
            elif user_input.lower() == 'clear':
                if app.clear_conversation():
                    print("Conversation cleared.")
                else:
                    print("Failed to clear conversation.")
                continue
            
            elif user_input.lower() == 'history':
                history = app.get_conversation_history()
                if not history:
                    print("No conversation history.")
                else:
                    print("\n--- Conversation History ---")
                    for msg in history:
                        role = msg.role.value.capitalize()
                        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                        print(f"{role}: {content}")
                    print("------------------------------")
                continue
            
            elif user_input.lower() == 'status':
                app.show_status()
                continue
            
            elif user_input.lower() == 'memory':
                app.show_memory_info()
                continue
            
            # Send message and get response
            try:
                response = app.send_message(user_input)
                print(f"NeuralProtocol: {response}")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        except KeyboardInterrupt:
            print("\nGoodbye from NeuralProtocol!")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


def main() -> None:
    """Main entry point for NeuralProtocol."""
    try:
        app = NeuralProtocolApp()
        app.initialize()
        app.show_status()
        interactive_chat(app)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"Failed to start NeuralProtocol: {str(e)}")


if __name__ == "__main__":
    main()
