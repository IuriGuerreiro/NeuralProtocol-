import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface EmailRateLimitHook {
  canSend: boolean;
  timeRemaining: number;
  checkRateLimit: (email: string, requestType?: string) => Promise<void>;
  startCountdown: (seconds: number) => void;
  resetTimer: () => void;
}

export const useEmailRateLimit = (): EmailRateLimitHook => {
  const [canSend, setCanSend] = useState(true);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const { checkEmailRateLimit } = useAuth();

  // Countdown timer effect
  useEffect(() => {
    let interval: number | null = null;

    if (timeRemaining > 0) {
      setCanSend(false);
      interval = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            setCanSend(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      setCanSend(true);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [timeRemaining]);

  const checkRateLimit = useCallback(async (email: string, requestType: string = 'email_verification') => {
    try {
      const status = await checkEmailRateLimit(email, requestType);
      setCanSend(status.can_send);
      setTimeRemaining(status.time_remaining);
    } catch {
      // On error, allow sending
      setCanSend(true);
      setTimeRemaining(0);
    }
  }, [checkEmailRateLimit]);

  const startCountdown = useCallback((seconds: number) => {
    setTimeRemaining(seconds);
    setCanSend(false);
  }, []);

  const resetTimer = useCallback(() => {
    setTimeRemaining(0);
    setCanSend(true);
  }, []);

  return {
    canSend,
    timeRemaining,
    checkRateLimit,
    startCountdown,
    resetTimer,
  };
};

export default useEmailRateLimit;