/**
 * Chat System Type Definitions
 * 
 * Type definitions for the NeuralProtocol chat system
 */

export interface ChatSession {
  session_id: string;
  session_name?: string;
  created_at: string;
  message_count: number;
  status: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  session_id: string;
}

export interface ChatResponse {
  user_message: Message;
  assistant_message: Message;
  session_id: string;
}

export interface ChatHistory {
  session_id: string;
  messages: Message[];
  total_messages: number;
}

export interface SystemStatus {
  session_id: string;
  llm_status: string;
  agent_status: string;
  stdio_servers: string[];
  http_servers: string[];
  tools_summary: any;
  message_count: number;
  approval_mode: boolean;
}

export interface ToolsSummary {
  total_tools: number;
  mcp_tools: any;
  http_tools: any;
  custom_tools: any;
  servers: Array<{
    name: string;
    type: string;
  }>;
}

export interface CreateSessionRequest {
  session_name?: string;
  model_name?: string;
  provider?: string;
}

export interface SendMessageRequest {
  content: string;
}