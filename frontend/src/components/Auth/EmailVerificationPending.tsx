import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom';
import { useEmailRateLimit } from '../../hooks/useEmailRateLimit';
import './Auth.css';

interface EmailVerificationPendingProps {
  email?: string;
  fromRegistration?: boolean;
}

const EmailVerificationPending: React.FC<EmailVerificationPendingProps> = ({ 
  email: propEmail,
  fromRegistration = false 
}) => {
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState('');
  const [resendSuccess, setResendSuccess] = useState(false);
  const { resendVerification } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { canSend, timeRemaining, checkRateLimit, startCountdown } = useEmailRateLimit();

  // Get email from props, location state, or URL params
  const email = propEmail || 
                location.state?.email || 
                new URLSearchParams(location.search).get('email') || 
                '';
  
  // Check if coming from login attempt
  const fromLogin = location.state?.fromLogin || false;
  const customMessage = location.state?.message;

  // Check rate limit when component mounts
  useEffect(() => {
    if (email) {
      checkRateLimit(email, 'email_verification');
    }
  }, [email, checkRateLimit]);

  const handleResendEmail = async () => {
    if (!email) {
      setResendMessage('Email address not found. Please try registering again.');
      setResendSuccess(false);
      return;
    }

    if (!canSend) {
      setResendMessage(`Please wait ${timeRemaining} seconds before requesting another verification email.`);
      setResendSuccess(false);
      return;
    }

    setIsResending(true);
    setResendMessage('');
    
    try {
      const result = await resendVerification(email);
      
      if (result.success) {
        setResendSuccess(true);
        setResendMessage('Verification email sent successfully! Please check your inbox.');
        // Start the 60-second countdown
        startCountdown(60);
      } else {
        setResendSuccess(false);
        setResendMessage(result.message || 'Failed to send verification email. Please try again.');
        // If it's a rate limit error, check the current status
        if (result.message.includes('wait') && result.message.includes('seconds')) {
          await checkRateLimit(email, 'email_verification');
        }
      }
    } catch {
      setResendSuccess(false);
      setResendMessage('Network error. Please check your connection and try again.');
    } finally {
      setIsResending(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  const handleBackToRegister = () => {
    navigate('/register');
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>
            {fromRegistration ? 'Check Your Email' : fromLogin ? 'Email Verification Required' : 'Email Verification Required'}
          </h2>
        </div>

        <div className="verification-pending-content">
          <div className="email-icon">
            📧
          </div>

          {fromRegistration ? (
            <div className="registration-success">
              <h3>Registration Successful!</h3>
              <p>
                Thank you for registering! We've sent a verification email to:
              </p>
              <div className="email-display">
                <strong>{email}</strong>
              </div>
              <p>
                Please check your email and click the verification link to activate your account.
              </p>
            </div>
          ) : fromLogin ? (
            <div className="verification-required">
              <h3>Login Blocked</h3>
              <p>
                {customMessage || 'Your email address needs to be verified before you can log in.'}
              </p>
              {email && (
                <div className="email-display">
                  <strong>{email}</strong>
                </div>
              )}
              <p>
                Please check your email for the verification link and click it to activate your account.
              </p>
            </div>
          ) : (
            <div className="verification-required">
              <h3>Please Verify Your Email</h3>
              <p>
                Your email address needs to be verified before you can log in.
              </p>
              {email && (
                <div className="email-display">
                  <strong>{email}</strong>
                </div>
              )}
              <p>
                Please check your email and click the verification link.
              </p>
            </div>
          )}

          <div className="verification-instructions">
            <h4>Next Steps:</h4>
            <ol>
              <li>Check your email inbox (and spam folder)</li>
              <li>Click the verification link in the email</li>
              <li>Return here to log in</li>
            </ol>
          </div>

          {resendMessage && (
            <div className={`message ${resendSuccess ? 'success' : 'error'}`}>
              {resendMessage}
            </div>
          )}

          <div className="verification-actions">
            <button
              onClick={handleResendEmail}
              disabled={isResending || !email || !canSend}
              className="auth-button secondary"
            >
              {isResending 
                ? 'Sending...' 
                : !canSend 
                  ? `Resend in ${timeRemaining}s`
                  : 'Resend Verification Email'
              }
            </button>

            <div className="action-links">
              <button
                onClick={handleBackToLogin}
                className="link-button"
              >
                Back to Login
              </button>
              
              {!fromRegistration && !fromLogin && (
                <>
                  <span className="separator">•</span>
                  <button
                    onClick={handleBackToRegister}
                    className="link-button"
                  >
                    Register New Account
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="help-text">
            <p>
              <strong>Didn't receive the email?</strong><br />
              Check your spam folder or try resending the verification email.
            </p>
            <p>
              <strong>Wrong email address?</strong><br />
              {fromRegistration ? 'Please register again with the correct email.' : 'Please register a new account with the correct email.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailVerificationPending;