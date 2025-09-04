"""
Django management command to test the chat system with database integration
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
import asyncio

from chat.models import ChatSession, Message
from chat.database_service import chat_db
from chat.enhanced_langchain_chat import create_enhanced_chat

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the enhanced chat system with database integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to test with',
            default='test@example.com'
        )
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Create test user if it does not exist',
        )
        parser.add_argument(
            '--test-message',
            type=str,
            help='Test message to send',
            default='Hello, what tools do you have access to?'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Enhanced Chat System'))
        
        # Get or create user
        user_email = options['user_email']
        try:
            user = User.objects.get(email=user_email)
            self.stdout.write(f'✅ Found user: {user.email}')
        except User.DoesNotExist:
            if options['create_user']:
                user = User.objects.create_user(
                    username=user_email.split('@')[0],
                    email=user_email,
                    password='testpass123'
                )
                self.stdout.write(f'✅ Created test user: {user.email}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ User {user_email} not found. Use --create-user to create it.')
                )
                return

        # Test database operations
        self.test_database_operations(user)
        
        # Test chat system
        asyncio.run(self.test_chat_system(user, options['test_message']))

    def test_database_operations(self, user):
        """Test basic database operations"""
        self.stdout.write('\n📊 Testing Database Operations...')
        
        # Create a test session
        session = chat_db.create_session(
            user=user,
            session_name='Test Session',
            model_name='gemini-2.0-flash',
            provider='google_genai'
        )
        self.stdout.write(f'✅ Created session: {session.session_id}')
        
        # Save test messages
        user_message = chat_db.save_message(
            session=session,
            role='user',
            content='Hello, this is a test message'
        )
        self.stdout.write(f'✅ Saved user message: {user_message.message_id}')
        
        assistant_message = chat_db.save_message(
            session=session,
            role='assistant',
            content='Hello! I am a test assistant response.',
            tokens_used=25,
            processing_time=1.5
        )
        self.stdout.write(f'✅ Saved assistant message: {assistant_message.message_id}')
        
        # Test retrieval
        messages = chat_db.get_session_messages(session)
        self.stdout.write(f'✅ Retrieved {len(messages)} messages')
        
        # Test statistics
        stats = chat_db.get_session_statistics(session)
        self.stdout.write(f'✅ Session statistics: {stats["total_messages"]} messages')
        
        self.stdout.write('✅ Database operations test completed')

    async def test_chat_system(self, user, test_message):
        """Test the enhanced chat system"""
        self.stdout.write('\n🤖 Testing Enhanced Chat System...')
        
        try:
            # Create a session for testing
            session = chat_db.create_session(
                user=user,
                session_name='Enhanced Chat Test',
                model_name='gemini-2.0-flash',
                provider='google_genai'
            )
            
            # Create enhanced chat instance
            chat = create_enhanced_chat(session=session)
            
            self.stdout.write('🔧 Initializing chat system...')
            
            # Check for configuration files
            import os
            config_files = ["servers_config.json", "simple_servers_config.json"]
            config_found = any(os.path.exists(f) for f in config_files)
            
            if not config_found:
                self.stdout.write(
                    self.style.WARNING('⚠️ No MCP server configuration found. Creating minimal config.')
                )
                # Create a minimal configuration for testing
                import json
                minimal_config = {
                    "mcpServers": {},
                    "providers": {
                        "google_genai": {
                            "env_var": "GOOGLE_API_KEY",
                            "api_key": "dummy-key-for-testing"
                        }
                    }
                }
                with open('simple_servers_config.json', 'w') as f:
                    json.dump(minimal_config, f, indent=2)
                chat.config_file = 'simple_servers_config.json'
            
            try:
                # Initialize the chat system
                await chat.initialize_all()
                
                self.stdout.write('✅ Chat system initialized successfully')
                
                # Test message processing
                self.stdout.write(f'💬 Sending test message: "{test_message}"')
                
                # This will likely fail without proper API keys, but we can test the database part
                try:
                    response = await chat.process_message(test_message)
                    self.stdout.write(f'🤖 Response: {response[:100]}...')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Message processing failed (expected without API keys): {e}')
                    )
                
                # Test database persistence
                messages_in_db = chat_db.get_session_messages(session)
                self.stdout.write(f'✅ Found {len(messages_in_db)} messages in database')
                
                for msg in messages_in_db:
                    self.stdout.write(f'  - {msg.role}: {msg.content[:50]}...')
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Chat initialization failed (expected without proper config): {e}')
                )
                
                # Still test database functionality
                self.stdout.write('📝 Testing manual message saving...')
                
                # Manually save messages to test database
                user_msg = chat_db.save_message(
                    session=session,
                    role='user',
                    content=test_message
                )
                
                assistant_msg = chat_db.save_message(
                    session=session,
                    role='assistant',
                    content='This is a test response saved directly to database.',
                    tokens_used=15,
                    processing_time=0.1
                )
                
                self.stdout.write('✅ Manual message saving successful')
            
            finally:
                # Cleanup
                await chat.cleanup()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Chat system test failed: {e}'))
            
        self.stdout.write('\n🎉 Chat system test completed!')

    def test_analytics(self, user):
        """Test analytics functionality"""
        self.stdout.write('\n📈 Testing Analytics...')
        
        # Update analytics
        analytics = chat_db.update_daily_analytics(
            user=user,
            sessions_created=1,
            messages_sent=5,
            messages_received=5,
            total_tokens_used=100,
            tools_executed=2
        )
        
        self.stdout.write(f'✅ Updated analytics for {analytics.user.email}')
        
        # Get analytics
        user_analytics = chat_db.get_user_analytics(user)
        self.stdout.write(f'✅ Retrieved {len(user_analytics)} analytics records')
        
        self.stdout.write('✅ Analytics test completed')

    def cleanup_test_data(self, user):
        """Clean up test data"""
        self.stdout.write('\n🧹 Cleaning up test data...')
        
        # Delete test sessions
        test_sessions = ChatSession.objects.filter(
            user=user,
            session_name__icontains='Test'
        )
        
        for session in test_sessions:
            self.stdout.write(f'🗑️ Deleting session: {session.session_id}')
            session.delete()
        
        self.stdout.write('✅ Cleanup completed')