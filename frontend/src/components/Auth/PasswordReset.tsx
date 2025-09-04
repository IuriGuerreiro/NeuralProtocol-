import React, { useState } from 'react';
import { API_ENDPOINTS } from '../../config/api';
import ErrorMessage from './ErrorMessage';
import './Auth.css';

interface PasswordResetProps {
  onBackToLogin: () => void;
}

const PasswordReset: React.FC<PasswordResetProps> = ({ onBackToLogin }) => {
  const [step, setStep] = useState<'email' | 'verify'>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);

  const handleRequestReset = async () => {
    setError('');
    setSuccess('');

    if (!email) {
      setError('Please enter your email address');
      return;
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.PASSWORD_RESET_REQUEST, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(data.message);
        if (data.user_id) {
          setUserId(data.user_id);
          setStep('verify');
        }
      } else {
        setError(data.error || 'Failed to send reset code');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    setError('');
    setSuccess('');

    if (!code || !password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!userId) {
      setError('Invalid reset session. Please start over.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.PASSWORD_RESET, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          code,
          password,
          confirm_password: confirmPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Password reset successfully! You can now login with your new password.');
        // Auto redirect to login after 3 seconds
        setTimeout(() => {
          onBackToLogin();
        }, 3000);
      } else {
        setError(data.error || 'Failed to reset password');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (step === 'email') {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h2>Reset Password</h2>
            <p>Enter your email to receive a reset code</p>
          </div>

          <div className="auth-form">
            {error && <ErrorMessage message={error} onClose={() => setError('')} />}
            {success && (
              <div className="success-message">
                <p>{success}</p>
              </div>
            )}
            
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                disabled={isLoading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleRequestReset();
                  }
                }}
              />
            </div>

            <button 
              type="button" 
              className="auth-button" 
              disabled={isLoading}
              onClick={handleRequestReset}
            >
              {isLoading ? 'Sending...' : 'Send Reset Code'}
            </button>
          </div>

          <div className="auth-switch">
            <p>
              Remember your password?{' '}
              <button 
                type="button" 
                className="link-button" 
                onClick={onBackToLogin}
              >
                Back to Login
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Reset Password</h2>
          <p>Enter the code sent to {email}</p>
        </div>

        <div className="auth-form">
          {error && <ErrorMessage message={error} onClose={() => setError('')} />}
          {success && (
            <div className="success-message">
              <p>{success}</p>
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="code">Verification Code</label>
            <input
              id="code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter 6-digit code"
              maxLength={6}
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">New Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter new password"
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              disabled={isLoading}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleResetPassword();
                }
              }}
            />
          </div>

          <button 
            type="button" 
            className="auth-button" 
            disabled={isLoading}
            onClick={handleResetPassword}
          >
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </button>
        </div>

        <div className="auth-switch">
          <p>
            <button 
              type="button" 
              className="link-button" 
              onClick={() => setStep('email')}
            >
              Back to Email
            </button>
            {' | '}
            <button 
              type="button" 
              className="link-button" 
              onClick={onBackToLogin}
            >
              Back to Login
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PasswordReset;