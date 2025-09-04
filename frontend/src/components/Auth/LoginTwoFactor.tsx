import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import ErrorMessage from './ErrorMessage';
import './Auth.css';

interface LoginTwoFactorProps {
  userId: number;
  email: string;
  message: string;
  codeAlreadySent?: boolean;
  onBack: () => void;
}

const LoginTwoFactor: React.FC<LoginTwoFactorProps> = ({ userId, email, message, codeAlreadySent, onBack }) => {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes in seconds
  const [resendMessage, setResendMessage] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);
  const [isResending, setIsResending] = useState(false);
  const { loginVerify2FA, resend2FACode, isLoading } = useAuth();

  // Timer countdown
  useEffect(() => {
    if (timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [timeLeft]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleVerify = async () => {
    setError('');

    if (!code || code.length !== 6) {
      setError('Please enter the 6-digit verification code');
      return;
    }

    try {
      await loginVerify2FA(userId, code);
      // Success - will redirect automatically via AuthContext
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Verification failed';
      setError(errorMessage);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleVerify();
    }
  };

  const handleCodeChange = (value: string) => {
    // Only allow numbers and limit to 6 digits
    const numericValue = value.replace(/\D/g, '').slice(0, 6);
    setCode(numericValue);
  };

  const handleResendCode = async () => {
    if (resendCooldown > 0 || isResending) return;

    try {
      setIsResending(true);
      setError('');
      setResendMessage('');
      
      const result = await resend2FACode(userId, 'login');
      
      if (result.success) {
        setResendMessage('A new verification code has been sent to your email.');
        setResendCooldown(60); // 60 second cooldown
        setTimeLeft(600); // Reset main timer to 10 minutes
        setCode(''); // Clear the current code input
      } else {
        setError(result.message);
        // Extract cooldown time from error message if it's a rate limit error
        const match = result.message.match(/wait (\d+) seconds/);
        if (match) {
          setResendCooldown(parseInt(match[1]));
        }
      }
    } catch (error) {
      setError('Failed to resend verification code. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Two-Factor Authentication</h2>
          <p>
            {codeAlreadySent === false 
              ? 'Enter the verification code sent to your email' 
              : 'Enter the verification code from your email'
            }
          </p>
        </div>

        <div className="auth-form">
          <div className="two-factor-info">
            <div className="email-info">
              <span className="email-icon">📧</span>
              <div>
                <p><strong>Code sent to:</strong></p>
                <p className="email-display">{email}</p>
              </div>
            </div>
            <p className="auth-message">{message}</p>
            {codeAlreadySent === true && (
              <div className="info-message" style={{ 
                background: '#e3f2fd', 
                border: '1px solid #2196f3', 
                borderRadius: '4px', 
                padding: '8px 12px', 
                margin: '8px 0',
                fontSize: '0.9rem',
                color: '#1976d2'
              }}>
                ℹ️ Using your previously sent verification code. Check your email for the 6-digit code.
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="verificationCode">Verification Code</label>
            <input
              type="text"
              id="verificationCode"
              value={code}
              onChange={(e) => handleCodeChange(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="000000"
              maxLength={6}
              className="auth-input code-input"
              disabled={isLoading || timeLeft === 0}
              autoComplete="off"
            />
            <div className="code-help">
              Enter the 6-digit code from your email
            </div>
          </div>

          <div className="timer-info">
            {timeLeft > 0 ? (
              <p className="timer">
                Code expires in: <span className="time-left">{formatTime(timeLeft)}</span>
              </p>
            ) : (
              <p className="timer expired">
                Code has expired. Please try logging in again.
              </p>
            )}
          </div>

          {error && <ErrorMessage message={error} />}
          
          {resendMessage && (
            <div className="message success" style={{
              background: '#e8f5e8',
              border: '1px solid #4caf50',
              borderRadius: '4px',
              padding: '8px 12px',
              margin: '8px 0',
              fontSize: '0.9rem',
              color: '#2e7d32'
            }}>
              <div className="message-icon">✅</div>
              <div className="message-text">{resendMessage}</div>
            </div>
          )}

          <div className="resend-section" style={{
            textAlign: 'center',
            margin: '16px 0',
            padding: '16px 0',
            borderTop: '1px solid #e0e0e0'
          }}>
            <p style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#666' }}>
              Didn't receive the code?
            </p>
            <button
              type="button"
              className="link-button"
              onClick={handleResendCode}
              disabled={resendCooldown > 0 || isResending || timeLeft === 0}
              style={{ 
                fontSize: '0.9rem',
                textDecoration: 'underline',
                color: resendCooldown > 0 || isResending ? '#999' : '#2196f3'
              }}
            >
              {isResending 
                ? 'Sending...' 
                : resendCooldown > 0 
                  ? `Resend in ${resendCooldown}s`
                  : 'Resend Code'
              }
            </button>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="auth-button secondary"
              onClick={onBack}
              disabled={isLoading}
            >
              Back to Login
            </button>
            
            <button
              type="button"
              className="auth-button primary"
              onClick={handleVerify}
              disabled={isLoading || !code || code.length !== 6 || timeLeft === 0}
            >
              {isLoading ? 'Verifying...' : 'Verify & Login'}
            </button>
          </div>
        </div>

        <div className="auth-footer">
          <p className="security-note">
            🔒 For your security, this code will expire in 10 minutes.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginTwoFactor;