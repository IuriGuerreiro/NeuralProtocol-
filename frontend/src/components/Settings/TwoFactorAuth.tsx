import React, { useState, useEffect } from 'react';
import { apiRequest, API_ENDPOINTS } from '../../config/api';
import TwoFactorVerifyModal from './TwoFactorVerifyModal';

interface TwoFactorStatus {
  two_factor_enabled: boolean;
  email: string;
}

const TwoFactorAuth: React.FC = () => {
  const [twoFactorStatus, setTwoFactorStatus] = useState<TwoFactorStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<'enable' | 'disable' | null>(null);

  useEffect(() => {
    fetchTwoFactorStatus();
  }, []);

  const fetchTwoFactorStatus = async () => {
    try {
      setLoading(true);
      const response = await apiRequest(API_ENDPOINTS.TWO_FACTOR_STATUS);
      setTwoFactorStatus(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch 2FA status');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle2FA = async (enable: boolean) => {
    try {
      setLoading(true);
      setError('');
      
      const response = await apiRequest(API_ENDPOINTS.TWO_FACTOR_TOGGLE, {
        method: 'POST',
        body: JSON.stringify({ enable }),
      });

      if (response.requires_verification) {
        setPendingAction(enable ? 'enable' : 'disable');
        setShowVerifyModal(true);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to toggle 2FA');
    } finally {
      setLoading(false);
    }
  };

  const handleVerificationSuccess = () => {
    setShowVerifyModal(false);
    setPendingAction(null);
    fetchTwoFactorStatus();
  };

  const handleVerificationCancel = () => {
    setShowVerifyModal(false);
    setPendingAction(null);
  };

  if (loading && !twoFactorStatus) {
    return (
      <div className="two-factor-auth">
        <div className="loading">Loading 2FA settings...</div>
      </div>
    );
  }

  return (
    <div className="two-factor-auth">
      <div className="two-factor-card">
        <div className="two-factor-header">
          <div className="status-indicator">
            <span className={`status-dot ${twoFactorStatus?.two_factor_enabled ? 'enabled' : 'disabled'}`}></span>
            <span className="status-text">
              {twoFactorStatus?.two_factor_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <h4>Email Two-Factor Authentication</h4>
        </div>
        
        <div className="two-factor-body">
          <p className="description">
            {twoFactorStatus?.two_factor_enabled 
              ? 'Your account is protected with email-based two-factor authentication. You will receive a verification code via email when signing in.'
              : 'Add an extra layer of security to your account. When enabled, you will receive a verification code via email when signing in.'
            }
          </p>
          
          {twoFactorStatus?.email && (
            <p className="email-info">
              <strong>Email:</strong> {twoFactorStatus.email}
            </p>
          )}
          
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div className="two-factor-actions">
            <button
              className={`btn ${twoFactorStatus?.two_factor_enabled ? 'btn-danger' : 'btn-primary'}`}
              onClick={() => handleToggle2FA(!twoFactorStatus?.two_factor_enabled)}
              disabled={loading}
            >
              {loading ? 'Processing...' : (
                twoFactorStatus?.two_factor_enabled ? 'Disable 2FA' : 'Enable 2FA'
              )}
            </button>
          </div>
        </div>
      </div>

      {showVerifyModal && pendingAction && (
        <TwoFactorVerifyModal
          action={pendingAction}
          onSuccess={handleVerificationSuccess}
          onCancel={handleVerificationCancel}
        />
      )}
    </div>
  );
};

export default TwoFactorAuth;