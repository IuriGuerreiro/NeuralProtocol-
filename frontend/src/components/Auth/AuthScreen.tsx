import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Login from './Login';
import Register from './Register';
import PasswordReset from './PasswordReset';
import './Auth.css';

const AuthScreen: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Determine which component to show based on route
  const isRegisterRoute = location.pathname === '/register';
  const isPasswordResetRoute = location.pathname === '/password-reset';
  const isLoginRoute = location.pathname === '/login' || location.pathname === '/';
  
  // Handle navigation between auth screens
  const switchToRegister = () => navigate('/register');
  const switchToLogin = () => navigate('/login');
  const switchToPasswordReset = () => navigate('/password-reset');

  return (
    <div className="auth-screen-desktop">
      <div className="auth-content-wrapper">
        {/* Left side - Branding/Info */}
        <div className="auth-branding">
          <div className="auth-branding-content">
            <h1>Welcome to Todoist</h1>
            <p>Organize your work and life, finally.</p>
            <ul className="auth-features">
              <li>✅ Track your tasks efficiently</li>
              <li>📅 Set deadlines and reminders</li>
              <li>📊 Monitor your productivity</li>
              <li>🔄 Sync across all devices</li>
            </ul>
          </div>
        </div>

        {/* Right side - Auth forms */}
        <div className="auth-form-section">
          {isRegisterRoute ? (
            <Register onSwitchToLogin={switchToLogin} />
          ) : isPasswordResetRoute ? (
            <PasswordReset onBackToLogin={switchToLogin} />
          ) : (
            <Login 
              onSwitchToRegister={switchToRegister} 
              onSwitchToPasswordReset={switchToPasswordReset}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;