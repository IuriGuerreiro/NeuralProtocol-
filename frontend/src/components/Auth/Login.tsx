import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import GoogleOAuth from './GoogleOAuth';
import ErrorMessage from './ErrorMessage';
import LoginTwoFactor from './LoginTwoFactor';
import './Auth.css';

interface LoginProps {
  onSwitchToRegister: () => void;
  onSwitchToPasswordReset: () => void;
}

const Login: React.FC<LoginProps> = ({ onSwitchToRegister, onSwitchToPasswordReset }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [twoFactorData, setTwoFactorData] = useState<{
    userId: number;
    email: string;
    message: string;
    codeAlreadySent?: boolean;
  } | null>(null);
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async () => {
    setError('');

    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    try {
      const result = await login(email, password);
      
      // Check if email verification is required
      if (result.emailNotVerified) {
        // Navigate to dedicated email verification pending page
        navigate('/verify-email-pending', { 
          state: { 
            email: result.email || email,
            message: result.message || 'Please verify your email address before logging in.',
            fromLogin: true
          } 
        });
        return;
      }
      
      // Check if 2FA is required
      if (result.requires2FA && result.userId && result.message) {
        setTwoFactorData({
          userId: result.userId,
          email: email,
          message: result.message,
          codeAlreadySent: result.codeAlreadySent
        });
      }
      // If no 2FA required, success - will redirect automatically via AuthContext
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setError(errorMessage);
    }
  };

  const handleBackFrom2FA = () => {
    setTwoFactorData(null);
    setError('');
  };

  // If 2FA is required, show 2FA component
  if (twoFactorData) {
    return (
      <LoginTwoFactor
        userId={twoFactorData.userId}
        email={twoFactorData.email}
        message={twoFactorData.message}
        codeAlreadySent={twoFactorData.codeAlreadySent}
        onBack={handleBackFrom2FA}
      />
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Welcome Back</h2>
          <p>Sign in to your account</p>
        </div>

        <div className="auth-form">
          {error && <ErrorMessage message={error} onClose={() => setError('')} />}
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={isLoading}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleLogin();
                }
              }}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={isLoading}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleLogin();
                }
              }}
            />
          </div>

          <div className="form-group" style={{ textAlign: 'right', marginBottom: '1rem' }}>
            <button 
              type="button" 
              className="link-button" 
              onClick={onSwitchToPasswordReset}
              style={{ fontSize: '0.9rem', padding: '0' }}
            >
              Forgot Password?
            </button>
          </div>

          <button 
            type="button" 
            className="auth-button" 
            disabled={isLoading}
            onClick={handleLogin}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
        </div>

        <GoogleOAuth onError={setError} />

        <div className="auth-switch">
          <p>
            Don't have an account?{' '}
            <button 
              type="button" 
              className="link-button" 
              onClick={onSwitchToRegister}
            >
              Sign Up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;