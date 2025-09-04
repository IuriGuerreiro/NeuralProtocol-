import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiRequest, API_ENDPOINTS } from '../../config/api';
import './Settings.css';

interface PasswordSetupProps {
  onPasswordSet?: () => void;
}

const PasswordSetup: React.FC<PasswordSetupProps> = ({ onPasswordSet }) => {
  const { user, refreshUserData } = useAuth();
  const [step, setStep] = useState<'initial' | 'verification'>('initial');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  
  // Form states
  const [verificationCode, setVerificationCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Show password setup only for OAuth-only users
  if (!user?.is_oauth_only_user) {
    return null;
  }

  const handleRequestPasswordSetup = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await apiRequest(API_ENDPOINTS.PASSWORD_SETUP_REQUEST, {
        method: 'POST',
        body: JSON.stringify({}),
      });
      
      setSuccess(response.message);
      setStep('verification');
    } catch (err: any) {
      setError(err.message || 'Failed to send verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await apiRequest(API_ENDPOINTS.PASSWORD_SETUP_SET, {
        method: 'POST',
        body: JSON.stringify({
          code: verificationCode,
          password,
          password_confirm: confirmPassword,
        }),
      });
      
      setSuccess(response.message);
      
      // Refresh user data to update is_oauth_only_user status
      if (refreshUserData) {
        await refreshUserData();
      }
      
      // Reset form
      setVerificationCode('');
      setPassword('');
      setConfirmPassword('');
      setStep('initial');
      
      // Call callback if provided
      if (onPasswordSet) {
        onPasswordSet();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to set password');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep('initial');
    setVerificationCode('');
    setPassword('');
    setConfirmPassword('');
    setError('');
    setSuccess('');
  };

  return (
    <div className="password-setup">
      <div className="password-setup-header">
        <h3>Password Setup</h3>
        <p>Your account is currently secured with Google OAuth only. Set up a password for additional login options.</p>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      {step === 'initial' && (
        <div className="password-setup-initial">
          <div className="oauth-info">
            <div className="oauth-indicator">
              <span className="oauth-icon">🔐</span>
              <div className="oauth-text">
                <strong>Google OAuth Account</strong>
                <p>You're currently using Google OAuth for authentication</p>
              </div>
            </div>
          </div>
          
          <button
            className="btn btn-primary"
            onClick={handleRequestPasswordSetup}
            disabled={loading}
          >
            {loading ? 'Sending Code...' : 'Set Up Password'}
          </button>
          
          <div className="setup-info">
            <h4>Why set up a password?</h4>
            <ul>
              <li>Alternative login method if Google OAuth is unavailable</li>
              <li>Enhanced account security with multiple authentication options</li>
              <li>Access to advanced security features</li>
            </ul>
            <p className="security-note">
              <strong>Security:</strong> Setting up a password requires email verification with a 6-digit code.
            </p>
          </div>
        </div>
      )}

      {step === 'verification' && (
        <div className="password-setup-verification">
          <div className="verification-header">
            <h4>Verify and Set Password</h4>
            <p>Enter the 6-digit code sent to your email and your new password.</p>
          </div>

          <form onSubmit={handleSetPassword} className="password-setup-form">
            <div className="form-group">
              <label htmlFor="verificationCode">Verification Code</label>
              <input
                type="text"
                id="verificationCode"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="Enter 6-digit code"
                maxLength={6}
                required
                className="form-control code-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">New Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter new password"
                minLength={8}
                required
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                minLength={8}
                required
                className="form-control"
              />
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleBack}
                disabled={loading}
              >
                Back
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || verificationCode.length !== 6 || !password || !confirmPassword}
              >
                {loading ? 'Setting Password...' : 'Set Password'}
              </button>
            </div>
          </form>
          
          <div className="verification-info">
            <p className="code-info">
              📧 Code expires in 10 minutes. Check your spam folder if you don't see the email.
            </p>
            <button
              type="button"
              className="btn-link"
              onClick={handleRequestPasswordSetup}
              disabled={loading}
            >
              Resend code
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PasswordSetup;