import React from 'react';
import type { Message } from '../../types/chat';
import './ChatMessage.css';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'user':
        return '👤';
      case 'assistant':
        return '🤖';
      case 'system':
        return '⚙️';
      default:
        return '❓';
    }
  };

  const getRoleClass = (role: string) => {
    switch (role) {
      case 'user':
        return 'user-message';
      case 'assistant':
        return 'assistant-message';
      case 'system':
        return 'system-message';
      default:
        return 'unknown-message';
    }
  };

  // Don't display system messages in the UI
  if (message.role === 'system') {
    return null;
  }

  return (
    <div className={`chat-message ${getRoleClass(message.role)}`}>
      <div className="message-header">
        <div className="role-info">
          <span className="role-icon">{getRoleIcon(message.role)}</span>
          <span className="role-name">
            {message.role === 'user' ? 'You' : 'Assistant'}
          </span>
        </div>
        <div className="message-timestamp">
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
      
      <div className="message-content">
        {message.content.split('\n').map((line, index) => (
          <div key={index} className="message-line">
            {line || <br />}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatMessage;