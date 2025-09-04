const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const API_ENDPOINTS = {
  // Authentication endpoints (matching Django authentication/urls.py)
  LOGIN: `${API_BASE_URL}/api/auth/login/`,
  LOGIN_VERIFY_2FA: `${API_BASE_URL}/api/auth/login/verify-2fa/`,
  REGISTER: `${API_BASE_URL}/api/auth/register/`,
  REFRESH_TOKEN: `${API_BASE_URL}/api/auth/token/refresh/`,
  LOGOUT: `${API_BASE_URL}/api/auth/logout/`,
  VERIFY_EMAIL: `${API_BASE_URL}/api/auth/verify-email/`,
  RESEND_VERIFICATION: `${API_BASE_URL}/api/auth/resend-verification/`,
  CHECK_EMAIL_RATE_LIMIT: `${API_BASE_URL}/api/auth/check-rate-limit/`,
  RESEND_2FA_CODE: `${API_BASE_URL}/api/auth/resend-2fa-code/`,
  
  // Google OAuth endpoints (YummiAI style)
  GOOGLE_LOGIN: `${API_BASE_URL}/api/auth/google/login/`,
  GOOGLE_REGISTER: `${API_BASE_URL}/api/auth/google/register/`,
  GOOGLE_OAUTH: `${API_BASE_URL}/api/auth/google-oauth/`, // Legacy endpoint
  
  // User endpoints  
  USER_PROFILE: `${API_BASE_URL}/api/auth/profile/`,
  
  // 2FA endpoints
  TWO_FACTOR_TOGGLE: `${API_BASE_URL}/api/auth/2fa/toggle/`,
  TWO_FACTOR_VERIFY: `${API_BASE_URL}/api/auth/2fa/verify/`,
  TWO_FACTOR_STATUS: `${API_BASE_URL}/api/auth/2fa/status/`,
  
  // Password setup endpoints (OAuth users only)
  PASSWORD_SETUP_REQUEST: `${API_BASE_URL}/api/auth/password/request/`,
  PASSWORD_SETUP_SET: `${API_BASE_URL}/api/auth/password/set/`,
  
  // Password reset endpoints (all users)
  PASSWORD_RESET_REQUEST: `${API_BASE_URL}/api/auth/password/reset/request/`,
  PASSWORD_RESET: `${API_BASE_URL}/api/auth/password/reset/`,
  
  // Todo endpoints (future)
  TODOS: `${API_BASE_URL}/api/todos/`,
  
  // Chat endpoints
  CHAT_SESSIONS: `${API_BASE_URL}/api/chat/sessions/`,
  CHAT_SESSION_DETAIL: (sessionId: string) => `${API_BASE_URL}/api/chat/sessions/${sessionId}/`,
  CHAT_MESSAGES: (sessionId: string) => `${API_BASE_URL}/api/chat/sessions/${sessionId}/messages/`,
  CHAT_HISTORY: (sessionId: string) => `${API_BASE_URL}/api/chat/sessions/${sessionId}/history/`,
  CHAT_CLEAR_HISTORY: (sessionId: string) => `${API_BASE_URL}/api/chat/sessions/${sessionId}/clear_history/`,
  CHAT_STATUS: (sessionId: string) => `${API_BASE_URL}/api/chat/sessions/${sessionId}/status/`,
  CHAT_TOOLS: (sessionId: string) => `${API_BASE_URL}/api/chat/sessions/${sessionId}/tools/`,
  CHAT_APPROVAL_MODE: (sessionId: string) => `${API_BASE_URL}/api/chat/sessions/${sessionId}/approval_mode/`,
  CHAT_HEALTH: `${API_BASE_URL}/api/chat/health/`,
};

// API utility functions
export const apiRequest = async (
  url: string, 
  options: RequestInit = {}
): Promise<any> => {
  const token = localStorage.getItem('access_token');
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (response.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        const refreshResponse = await fetch(API_ENDPOINTS.REFRESH_TOKEN, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken }),
        });
        
        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          localStorage.setItem('access_token', data.access);
          
          // Retry original request with new token
          config.headers = {
            ...config.headers,
            'Authorization': `Bearer ${data.access}`,
          };
          return fetch(url, config);
        } else {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject('Authentication failed');
        }
      }
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

export default API_ENDPOINTS;