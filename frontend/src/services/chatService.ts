/**
 * Chat Service
 * 
 * Service layer for interacting with the NeuralProtocol chat API.
 * Provides functions for managing chat sessions, sending messages, and retrieving chat data.
 */

import { apiRequest } from '../config/api';
import API_ENDPOINTS from '../config/api';
import type {
  ChatSession,
  Message,
  ChatResponse,
  ChatHistory,
  SystemStatus,
  ToolsSummary,
  CreateSessionRequest,
  SendMessageRequest
} from '../types/chat';

/**
 * Chat Service Class
 * Provides all chat-related API operations
 */
export class ChatService {
  
  /**
   * Create a new chat session
   */
  async createSession(data: CreateSessionRequest = {}): Promise<ChatSession> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_SESSIONS, {
        method: 'POST',
        body: JSON.stringify({
          session_name: data.session_name,
          model_name: data.model_name || 'gemini-2.0-flash',
          provider: data.provider || 'google_genai'
        }),
      });
      return response;
    } catch (error) {
      console.error('Failed to create chat session:', error);
      throw new Error('Failed to create chat session');
    }
  }

  /**
   * Get all chat sessions
   */
  async getSessions(): Promise<ChatSession[]> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_SESSIONS);
      return response;
    } catch (error) {
      console.error('Failed to get chat sessions:', error);
      throw new Error('Failed to get chat sessions');
    }
  }

  /**
   * Get a specific chat session
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_SESSION_DETAIL(sessionId));
      return response;
    } catch (error) {
      console.error(`Failed to get chat session ${sessionId}:`, error);
      throw new Error('Failed to get chat session');
    }
  }

  /**
   * Send a message and get response
   */
  async sendMessage(sessionId: string, content: string): Promise<ChatResponse> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_MESSAGES(sessionId), {
        method: 'POST',
        body: JSON.stringify({ content }),
      });
      return response;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw new Error('Failed to send message');
    }
  }

  /**
   * Get chat history for a session
   */
  async getChatHistory(
    sessionId: string, 
    limit?: number, 
    offset?: number
  ): Promise<ChatHistory> {
    try {
      let url = API_ENDPOINTS.CHAT_HISTORY(sessionId);
      const params = new URLSearchParams();
      
      if (limit !== undefined) params.append('limit', limit.toString());
      if (offset !== undefined) params.append('offset', offset.toString());
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await apiRequest(url);
      return response;
    } catch (error) {
      console.error('Failed to get chat history:', error);
      throw new Error('Failed to get chat history');
    }
  }

  /**
   * Clear chat history for a session
   */
  async clearChatHistory(sessionId: string): Promise<{ message: string }> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_CLEAR_HISTORY(sessionId), {
        method: 'DELETE',
      });
      return response;
    } catch (error) {
      console.error('Failed to clear chat history:', error);
      throw new Error('Failed to clear chat history');
    }
  }

  /**
   * Get system status for a session
   */
  async getSystemStatus(sessionId: string): Promise<SystemStatus> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_STATUS(sessionId));
      return response;
    } catch (error) {
      console.error('Failed to get system status:', error);
      throw new Error('Failed to get system status');
    }
  }

  /**
   * Get tools summary for a session
   */
  async getToolsSummary(sessionId: string): Promise<ToolsSummary> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_TOOLS(sessionId));
      return response;
    } catch (error) {
      console.error('Failed to get tools summary:', error);
      throw new Error('Failed to get tools summary');
    }
  }

  /**
   * Toggle approval mode for a session
   */
  async toggleApprovalMode(sessionId: string): Promise<{ approval_mode: boolean; message: string }> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_APPROVAL_MODE(sessionId), {
        method: 'PUT',
      });
      return response;
    } catch (error) {
      console.error('Failed to toggle approval mode:', error);
      throw new Error('Failed to toggle approval mode');
    }
  }

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string): Promise<{ message: string }> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_SESSION_DETAIL(sessionId), {
        method: 'DELETE',
      });
      return response;
    } catch (error) {
      console.error('Failed to delete chat session:', error);
      throw new Error('Failed to delete chat session');
    }
  }

  /**
   * Check chat API health
   */
  async healthCheck(): Promise<{ status: string; message: string }> {
    try {
      const response = await apiRequest(API_ENDPOINTS.CHAT_HEALTH);
      return response;
    } catch (error) {
      console.error('Chat API health check failed:', error);
      throw new Error('Chat API is not available');
    }
  }
}

// Export a singleton instance
export const chatService = new ChatService();

// Re-export types for convenience
export type {
  ChatSession,
  Message,
  ChatResponse,
  ChatHistory,
  SystemStatus,
  ToolsSummary,
  CreateSessionRequest,
  SendMessageRequest
} from '../types/chat';

// Export default
export default chatService;