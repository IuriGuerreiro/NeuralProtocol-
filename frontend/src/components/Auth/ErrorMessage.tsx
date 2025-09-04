import React from 'react';
import './Auth.css';

interface ErrorMessageProps {
  message: string;
  onClose?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onClose }) => {
  // Determine error type based on message content
  const getErrorType = (msg: string): string => {
    if (msg.includes('Service may be unavailable') || msg.includes('Service unavailable') || msg.includes('try again later')) {
      return 'service-error';
    }
    if (msg.includes('network') || msg.includes('connection')) {
      return 'network-error';
    }
    return '';
  };

  const errorType = getErrorType(message);

  return (
    <div className={`error-message ${errorType}`}>
      <span className="error-text">{message}</span>
      {onClose && (
        <button 
          onClick={onClose}
          className="error-close"
          type="button"
          aria-label="Close error message"
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;