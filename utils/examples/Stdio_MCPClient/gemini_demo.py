#!/usr/bin/env python3
"""
Simple Gemini Demo - Shows the Gemini integration working
"""

import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

class SimpleGeminiClient:
    """Simple Gemini client for testing the integration."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ Gemini client initialized successfully!")
    
    def get_response(self, messages: list[dict[str, str]]) -> str:
        """Get a response from Gemini.
        
        Args:
            messages: A list of message dictionaries.
            
        Returns:
            The LLM's response as a string.
        """
        try:
            # Build the conversation context
            conversation_context = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    # Add system message to context
                    conversation_context += f"{msg['content']}\n\n"
                elif msg["role"] == "user":
                    # Add user message
                    conversation_context += f"User: {msg['content']}\n"
                elif msg["role"] == "assistant":
                    # Add assistant message
                    conversation_context += f"Assistant: {msg['content']}\n"
            
            # Add the current user prompt
            conversation_context += "Assistant: "
            
            # Generate response
            response = self.model.generate_content(conversation_context)
            return response.text
            
        except Exception as e:
            error_message = f"Error getting Gemini response: {str(e)}"
            logging.error(error_message)
            return f"I encountered an error: {error_message}. Please try again or rephrase your request."
    
    def simple_chat(self, prompt: str) -> str:
        """Simple chat with Gemini."""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"


def interactive_demo():
    """Interactive demo of Gemini integration."""
    try:
        client = SimpleGeminiClient()
        
        print("\n🎮 Simple Gemini Demo Ready!")
        print("Type 'quit' to exit, 'help' for help")
        print("=" * 50)
        
        # Test simple response
        print("\n🧪 Testing simple Gemini response...")
        test_response = client.simple_chat("Hello! Can you tell me a short joke?")
        print(f"Gemini: {test_response}")
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print("Goodbye from Gemini Demo!")
                    break
                
                elif user_input.lower() == 'help':
                    print("\n📖 Available Commands:")
                    print("  quit - Exit the demo")
                    print("  help - Show this help message")
                    print("  Or just type your message to chat with Gemini!")
                    continue
                
                # Get response from Gemini
                response = client.simple_chat(user_input)
                print(f"🤖 Gemini: {response}")
                
            except KeyboardInterrupt:
                print("\nGoodbye from Gemini Demo!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}")
        print("Make sure you have GOOGLE_API_KEY set in your .env file")


def test_conversation_context():
    """Test conversation context handling."""
    try:
        client = SimpleGeminiClient()
        
        print("\n🧪 Testing conversation context...")
        
        # Create a conversation with context
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Keep responses concise."},
            {"role": "user", "content": "What's 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."},
            {"role": "user", "content": "What did I just ask you?"}
        ]
        
        response = client.get_response(messages)
        print(f"Gemini (with context): {response}")
        
    except Exception as e:
        print(f"Error testing conversation context: {e}")


if __name__ == "__main__":
    print("🚀 Simple Gemini Demo")
    print("This demonstrates the Gemini integration working")
    
    try:
        # Test conversation context first
        test_conversation_context()
        
        # Then run interactive demo
        interactive_demo()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
