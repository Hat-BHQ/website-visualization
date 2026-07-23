import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { queryClient } from '@/app/queryClient';
import { loadCurrentUser } from '@/auth/sessionActions';
import { clearAuthSession, setSessionExpiredHandler } from '@/auth/sessionStore';

function AuthLifecycleBridge() {
  const navigate = useNavigate();

  useEffect(() => {
    setSessionExpiredHandler(() => {
      clearAuthSession();
      queryClient.clear();
      navigate('/login', { replace: true });
    });

    return () => setSessionExpiredHandler(null);
  }, [navigate]);

  useEffect(() => {
    void loadCurrentUser().catch(() => {
      clearAuthSession();
    });
  }, []);

  return null;
}

export function AuthProvider({ children }: { children: import('react').ReactNode }) {
  return (
    <>
      <AuthLifecycleBridge />
      {children}
    </>
  );
}
