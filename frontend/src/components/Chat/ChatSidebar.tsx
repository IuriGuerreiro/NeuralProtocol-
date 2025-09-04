import React, { useState } from 'react';
import type { ChatSession } from '../../types/chat';
import './ChatSidebar.css';

interface ChatSidebarProps {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: (sessionName?: string) => void;
  onDeleteSession: (sessionId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  currentSession,
  onSessionSelect,
  onNewSession,
  onDeleteSession,
  isOpen,
  onToggle
}) => {
  const [newSessionName, setNewSessionName] = useState('');
  const [showNewSessionInput, setShowNewSessionInput] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleNewSession = () => {
    if (newSessionName.trim()) {
      onNewSession(newSessionName.trim());
      setNewSessionName('');
      setShowNewSessionInput(false);
    } else {
      onNewSession();
      setShowNewSessionInput(false);
    }
  };

  const handleDeleteSession = (sessionId: string) => {
    if (deleteConfirm === sessionId) {
      onDeleteSession(sessionId);
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(sessionId);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  const getSessionDisplayName = (session: ChatSession) => {
    if (session.session_name) {
      return session.session_name;
    }
    return `Chat ${session.session_id.slice(0, 8)}...`;
  };

  if (!isOpen) {
    return (
      <div className="sidebar-collapsed">
        <button className="sidebar-toggle" onClick={onToggle}>
          ☰
        </button>
      </div>
    );
  }

  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <h3>Chat Sessions</h3>
        <button className="sidebar-close" onClick={onToggle}>
          ×
        </button>
      </div>

      <div className="sidebar-actions">
        {!showNewSessionInput ? (
          <button 
            className="new-session-btn"
            onClick={() => setShowNewSessionInput(true)}
          >
            + New Chat
          </button>
        ) : (
          <div className="new-session-form">
            <input
              type="text"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              placeholder="Session name (optional)"
              className="session-name-input"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleNewSession();
                } else if (e.key === 'Escape') {
                  setShowNewSessionInput(false);
                  setNewSessionName('');
                }
              }}
              autoFocus
            />
            <div className="form-actions">
              <button onClick={handleNewSession} className="btn-create">
                Create
              </button>
              <button 
                onClick={() => {
                  setShowNewSessionInput(false);
                  setNewSessionName('');
                }}
                className="btn-cancel"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="empty-sessions">
            <p>No chat sessions yet</p>
            <p>Create your first chat to get started</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div 
              key={session.session_id}
              className={`session-item ${
                currentSession?.session_id === session.session_id ? 'active' : ''
              }`}
              onClick={() => onSessionSelect(session.session_id)}
            >
              <div className="session-header">
                <div className="session-name">
                  {getSessionDisplayName(session)}
                </div>
                <button
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteSession(session.session_id);
                  }}
                >
                  {deleteConfirm === session.session_id ? '✓' : '🗑️'}
                </button>
              </div>
              
              <div className="session-info">
                <div className="session-date">
                  {formatDate(session.created_at)}
                </div>
                <div className="session-stats">
                  <span className="message-count">
                    {session.message_count} messages
                  </span>
                  <span className="session-status">
                    {session.status}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {deleteConfirm && (
        <div className="delete-confirmation">
          <p>Click the checkmark again to confirm deletion</p>
          <button 
            onClick={() => setDeleteConfirm(null)}
            className="btn-cancel-delete"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatSidebar;