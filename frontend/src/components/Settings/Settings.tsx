import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import TwoFactorAuth from './TwoFactorAuth';
import PasswordSetup from './PasswordSetup';
import './Settings.css';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const [activeSection, setActiveSection] = useState<string>('account');

  const sections = [
    { id: 'account', label: 'Account', icon: '👤' },
    { id: 'security', label: 'Security', icon: '🔒' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'preferences', label: 'Preferences', icon: '⚙️' },
  ];

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'account':
        return (
          <div className="settings-section">
            <h2>Account Settings</h2>
            <div className="account-info">
              <div className="info-group">
                <label>Username</label>
                <p>{user?.username}</p>
              </div>
              <div className="info-group">
                <label>Email</label>
                <p>{user?.email}</p>
              </div>
              <div className="info-group">
                <label>Name</label>
                <p>{user?.first_name} {user?.last_name}</p>
              </div>
              <div className="info-group">
                <label>Email Verified</label>
                <p className={user?.is_email_verified ? 'verified' : 'unverified'}>
                  {user?.is_email_verified ? '✅ Verified' : '⚠️ Not Verified'}
                </p>
              </div>
              <div className="info-group">
                <label>Account Type</label>
                <p className={user?.is_oauth_only_user ? 'oauth-only' : 'full-account'}>
                  {user?.is_oauth_only_user ? '🔐 Google OAuth Only' : '🔑 Full Account (Google OAuth + Password)'}
                </p>
              </div>
            </div>
            
            {user?.is_oauth_only_user && (
              <div className="password-setup-section">
                <h3>Password Setup</h3>
                <PasswordSetup />
              </div>
            )}
            
            <div className="security-section">
              <h3>Two-Factor Authentication</h3>
              <TwoFactorAuth />
            </div>
          </div>
        );
      case 'security':
        return (
          <div className="settings-section">
            <h2>Security Settings</h2>
            <div className="security-options">
              <div className="security-option">
                <h3>Two-Factor Authentication</h3>
                <p>Add an extra layer of security to your account</p>
                <TwoFactorAuth />
              </div>
              <div className="security-option">
                <h3>Password</h3>
                <p>
                  {user?.is_oauth_only_user 
                    ? 'Set up a password for additional login options' 
                    : 'Change your account password'
                  }
                </p>
                {user?.is_oauth_only_user ? (
                  <PasswordSetup />
                ) : (
                  <button className="btn btn-secondary">Change Password</button>
                )}
              </div>
              <div className="security-option">
                <h3>Login Sessions</h3>
                <p>Manage your active login sessions</p>
                <button className="btn btn-secondary">View Sessions</button>
              </div>
            </div>
          </div>
        );
      case 'notifications':
        return (
          <div className="settings-section">
            <h2>Notification Settings</h2>
            <p>Manage your notification preferences (Coming soon)</p>
          </div>
        );
      case 'preferences':
        return (
          <div className="settings-section">
            <h2>Preferences</h2>
            <p>Customize your experience (Coming soon)</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="settings-container">
      <div className="settings-sidebar">
        <h2>Settings</h2>
        <nav className="settings-nav">
          {sections.map((section) => (
            <button
              key={section.id}
              className={`nav-item ${activeSection === section.id ? 'active' : ''}`}
              onClick={() => setActiveSection(section.id)}
            >
              <span className="nav-icon">{section.icon}</span>
              <span className="nav-label">{section.label}</span>
            </button>
          ))}
        </nav>
      </div>
      <div className="settings-content">
        {renderSectionContent()}
      </div>
    </div>
  );
};

export default Settings;