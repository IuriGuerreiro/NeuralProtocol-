import React from 'react';

const EnvDebug: React.FC = () => {
  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      right: '10px', 
      background: '#f0f0f0', 
      padding: '10px', 
      borderRadius: '5px',
      fontSize: '12px',
      zIndex: 9999,
      maxWidth: '300px'
    }}>
      <h4>Environment Debug</h4>
      <div><strong>NODE_ENV:</strong> {import.meta.env.NODE_ENV}</div>
      <div><strong>MODE:</strong> {import.meta.env.MODE}</div>
      <div><strong>VITE_GOOGLE_CLIENT_ID:</strong> {import.meta.env.VITE_GOOGLE_CLIENT_ID || 'UNDEFINED'}</div>
      <div><strong>VITE_API_BASE_URL:</strong> {import.meta.env.VITE_API_BASE_URL || 'UNDEFINED'}</div>
      <div><strong>All env vars:</strong></div>
      <pre style={{ fontSize: '10px', maxHeight: '100px', overflow: 'auto' }}>
        {JSON.stringify(import.meta.env, null, 2)}
      </pre>
    </div>
  );
};

export default EnvDebug;