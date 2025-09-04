import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { BrowserRouter, Routes, Route, useParams } from "react-router-dom";

import AuthScreen from './components/Auth/AuthScreen';
import Dashboard from './components/Dashboard/Dashboard';
import EmailVerification from './components/Auth/EmailVerification';
import EmailVerificationPending from './components/Auth/EmailVerificationPending';
import { ChatInterface } from './components/Chat';
import './App.css';

// Email verification wrapper to get token from route params
const EmailVerificationWrapper: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  return <EmailVerification token={token || ''} />;
};

// Chat session wrapper to get session ID from route params
const ChatSessionWrapper: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  return <ChatInterface sessionId={sessionId} />;
};

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isAuthenticated && user) {
    return (
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chat" element={<ChatInterface />} />
        <Route path="/chat/:sessionId" element={<ChatSessionWrapper />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<AuthScreen />} />
      <Route path="/login" element={<AuthScreen />} />
      <Route path="/register" element={<AuthScreen />} />
      <Route path="/password-reset" element={<AuthScreen />} />
      <Route path="/verify-email/:token" element={<EmailVerificationWrapper />} />
      <Route path="/verify-email-pending" element={<EmailVerificationPending />} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
