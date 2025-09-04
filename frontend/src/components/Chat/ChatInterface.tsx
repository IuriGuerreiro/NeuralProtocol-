import React, { useState, useEffect, useRef } from 'react';
import type { ChatSession, Message, ChatResponse } from '../../types/chat';
import { chatService } from '../../services/chatService';
import MessageInput from './MessageInput';
import ChatMessage from './ChatMessage';
import ChatSidebar from './ChatSidebar';
import './ChatInterface.css';

interface ChatInterfaceProps {
  sessionId?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId: initialSessionId }) => {
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load specific session if provided
  useEffect(() => {
    if (initialSessionId) {
      loadSession(initialSessionId);
    }
  }, [initialSessionId]);

  const loadSessions = async () => {
    try {
      const sessionsList = await chatService.getSessions();
      setSessions(sessionsList);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setError('Failed to load chat sessions');
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Load session details
      const session = await chatService.getSession(sessionId);
      setCurrentSession(session);
      
      // Load chat history
      const history = await chatService.getChatHistory(sessionId);
      setMessages(history.messages);
      
    } catch (error) {
      console.error('Failed to load session:', error);
      setError('Failed to load chat session');
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async (sessionName?: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const newSession = await chatService.createSession({
        session_name: sessionName || `Chat ${new Date().toLocaleString()}`,
      });
      
      setCurrentSession(newSession);
      setMessages([]);
      setSessions([newSession, ...sessions]);
      
    } catch (error) {
      console.error('Failed to create session:', error);
      setError('Failed to create new chat session');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (content: string) => {
    if (!currentSession) {
      setError('No active chat session');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response: ChatResponse = await chatService.sendMessage(currentSession.session_id, content);
      
      // Add both user and assistant messages to the display
      setMessages(prev => [...prev, response.user_message, response.assistant_message]);
      
      // Update session message count
      setCurrentSession(prev => prev ? { ...prev, message_count: prev.message_count + 2 } : null);
      
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await chatService.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.session_id !== sessionId));
      
      // If deleted session was current, clear it
      if (currentSession?.session_id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      setError('Failed to delete session');
    }
  };

  const clearHistory = async () => {
    if (!currentSession) return;
    
    try {
      await chatService.clearChatHistory(currentSession.session_id);
      setMessages([]);
      setCurrentSession(prev => prev ? { ...prev, message_count: 1 } : null);
    } catch (error) {
      console.error('Failed to clear history:', error);
      setError('Failed to clear chat history');
    }
  };

  return (
    <div className="chat-interface">
      <ChatSidebar
        sessions={sessions}
        currentSession={currentSession}
        onSessionSelect={loadSession}
        onNewSession={createNewSession}
        onDeleteSession={deleteSession}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      
      <div className={`chat-main ${sidebarOpen ? 'with-sidebar' : ''}`}>
        <div className="chat-header">
          <div className="header-left">
            <button 
              className="sidebar-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              ☰
            </button>
            <h2>
              {currentSession ? 
                (currentSession.session_name || `Session ${currentSession.session_id.slice(0, 8)}...`) : 
                'NeuralProtocol Chat'
              }
            </h2>
          </div>
          
          {currentSession && (
            <div className="header-actions">
              <button onClick={clearHistory} className="btn-secondary">
                Clear History
              </button>
              <div className="session-info">
                Messages: {currentSession.message_count}
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        <div className="messages-container">
          {!currentSession && (
            <div className="welcome-screen">
              <h3>Welcome to NeuralProtocol Chat</h3>
              <p>Create a new chat session to start talking with the AI assistant.</p>
              <button 
                onClick={() => createNewSession()}
                className="btn-primary"
                disabled={isLoading}
              >
                {isLoading ? 'Creating...' : 'Start New Chat'}
              </button>
            </div>
          )}

          {currentSession && (
            <>
              <div className="messages-list">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                  />
                ))}
                {isLoading && (
                  <div className="typing-indicator">
                    <div className="typing-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span>AI is thinking...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              
              <MessageInput 
                onSendMessage={sendMessage}
                disabled={isLoading}
                placeholder={isLoading ? "AI is responding..." : "Type your message..."}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;