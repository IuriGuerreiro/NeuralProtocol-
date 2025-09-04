import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Settings from '../Settings/Settings';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [currentView, setCurrentView] = useState<'dashboard' | 'settings'>('dashboard');

  const renderContent = () => {
    switch (currentView) {
      case 'settings':
        return <Settings />;
      case 'dashboard':
      default:
        return (
          <main className="dashboard-main">
            <div className="dashboard-content">
              <div className="welcome-card">
                <h2>Dashboard</h2>
                <p>You are now logged in successfully!</p>
                <div className="user-details">
                  <p><strong>Username:</strong> {user?.username}</p>
                  <p><strong>Email:</strong> {user?.email}</p>
                  {user?.first_name && (
                    <p><strong>Name:</strong> {user.first_name} {user.last_name}</p>
                  )}
                  <p><strong>2FA Status:</strong> 
                    <span className={user?.two_factor_enabled ? 'status-enabled' : 'status-disabled'}>
                      {user?.two_factor_enabled ? ' ✅ Enabled' : ' ❌ Disabled'}
                    </span>
                  </p>
                </div>
                <div className="dashboard-actions">
                  <button 
                    onClick={() => setCurrentView('settings')} 
                    className="btn btn-primary"
                  >
                    Account Settings
                  </button>
                </div>
              </div>
            </div>
          </main>
        );
    }
  };

  if (currentView === 'settings') {
    return (
      <div className="dashboard">
        <header className="dashboard-header">
          <div className="header-content">
            <button 
              onClick={() => setCurrentView('dashboard')} 
              className="back-button"
            >
              ← Back to Dashboard
            </button>
            <div className="user-info">
              <span>Hello, {user?.first_name || user?.username}!</span>
              <button onClick={logout} className="logout-button">
                Logout
              </button>
            </div>
          </div>
        </header>
        {renderContent()}
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Welcome to Todoist</h1>
          <div className="user-info">
            <span>Hello, {user?.first_name || user?.username}!</span>
            <button 
              onClick={() => setCurrentView('settings')} 
              className="settings-button"
              title="Settings"
            >
              ⚙️
            </button>
            <button onClick={logout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </header>
      {renderContent()}
    </div>
  );
};

export default Dashboard;