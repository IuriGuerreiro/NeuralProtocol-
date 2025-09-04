import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './Auth.css';

interface EmailVerificationProps {
  token: string;
}

const EmailVerification: React.FC<EmailVerificationProps> = ({ token }) => {
  const [verificationStatus, setVerificationStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const { verifyEmail } = useAuth();

  useEffect(() => {
    const handleVerification = async () => {
      const result = await verifyEmail(token);
      
      if (result.success) {
        setVerificationStatus('success');
        setMessage(result.message);
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          window.location.href = '/login';
        }, 3000);
      } else {
        setVerificationStatus('error');
        setMessage(result.message);
      }
    };

    handleVerification();
  }, [token, verifyEmail]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Email Verification</h2>
        </div>

        <div className="verification-content">
          {verificationStatus === 'loading' && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Verifying your email...</p>
            </div>
          )}

          {verificationStatus === 'success' && (
            <div className="success-state">
              <div className="success-icon">✅</div>
              <h3>Email Verified Successfully!</h3>
              <p>{message}</p>
              <p>You will be redirected to login in a few seconds...</p>
            </div>
          )}

          {verificationStatus === 'error' && (
            <div className="error-state">
              <div className="error-icon">❌</div>
              <h3>Verification Failed</h3>
              <p className="error-message">{message}</p>
              <button 
                onClick={() => window.location.href = '/'}
                className="auth-button"
              >
                Go to Homepage
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;