import React, { useState, useEffect } from 'react';
import { apiRequest, API_ENDPOINTS } from '../../config/api';

interface TwoFactorVerifyModalProps {
  action: 'enable' | 'disable';
  onSuccess: () => void;
  onCancel: () => void;
}

const TwoFactorVerifyModal: React.FC<TwoFactorVerifyModalProps> = ({
  action,
  onSuccess,
  onCancel,
}) => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes in seconds

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (code.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const purpose = action === 'enable' ? 'enable_2fa' : 'disable_2fa';
      
      const response = await apiRequest(API_ENDPOINTS.TWO_FACTOR_VERIFY, {
        method: 'POST',
        body: JSON.stringify({ code, purpose }),
      });

      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Invalid or expired code');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setCode(value);
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            {action === 'enable' ? 'Enable' : 'Disable'} Two-Factor Authentication
          </h3>
          <button className="modal-close" onClick={onCancel}>
            ×
          </button>
        </div>
        
        <div className="modal-body">
          <div className="verification-info">
            <div className="email-icon">📧</div>
            <p>
              We've sent a 6-digit verification code to your email address. 
              Please enter it below to {action === 'enable' ? 'enable' : 'disable'} 2FA.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="code-input-container">
              <label htmlFor="verification-code">Verification Code</label>
              <input
                id="verification-code"
                type="text"
                value={code}
                onChange={handleCodeChange}
                placeholder="000000"
                className="code-input"
                maxLength={6}
                autoComplete="one-time-code"
                autoFocus
              />
              <div className="code-hint">
                Enter the 6-digit code from your email
              </div>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div className="timer-info">
              {timeLeft > 0 ? (
                <p className="timer">
                  ⏰ Code expires in: <span className="time-left">{formatTime(timeLeft)}</span>
                </p>
              ) : (
                <p className="timer expired">
                  ⚠️ Code has expired. Please try again.
                </p>
              )}
            </div>

            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onCancel}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || code.length !== 6 || timeLeft <= 0}
              >
                {loading ? 'Verifying...' : 'Verify Code'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TwoFactorVerifyModal;