import {
  useEffect,
  useSyncExternalStore,
} from 'react';

import { useNavigate } from 'react-router-dom';

import { queryClient } from '@/app/queryClient';

import {
  loadCurrentUser,
  logoutSession,
} from '@/auth/sessionActions';

import {
  clearAuthSession,
  getAuthSnapshot,
  setSessionExpiredHandler,
  subscribe,
} from '@/auth/sessionStore';

function AuthLifecycleBridge() {
  const navigate = useNavigate();

  const authSnapshot = useSyncExternalStore(
    subscribe,
    getAuthSnapshot,
    getAuthSnapshot,
  );

  useEffect(() => {
    setSessionExpiredHandler(() => {
      clearAuthSession();
      queryClient.clear();

      navigate('/login', {
        replace: true,
      });
    });

    return () => {
      setSessionExpiredHandler(null);
    };
  }, [navigate]);

  useEffect(() => {
    void loadCurrentUser().catch(() => {
      clearAuthSession();
    });
  }, []);

  useEffect(() => {
    if (
      !authSnapshot.accessToken ||
      !authSnapshot.expiresAt
    ) {
      return undefined;
    }

    const remainingTime =
      authSnapshot.expiresAt - Date.now();

    const expireSession = () => {
      void logoutSession().finally(() => {
        navigate('/login', {
          replace: true,
        });
      });
    };

    if (remainingTime <= 0) {
      expireSession();
      return undefined;
    }

    const timeoutId = window.setTimeout(
      expireSession,
      remainingTime,
    );

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [
    authSnapshot.accessToken,
    authSnapshot.expiresAt,
    navigate,
  ]);

  return null;
}

export function AuthProvider({
  children,
}: {
  children: import('react').ReactNode;
}) {
  return (
    <>
      <AuthLifecycleBridge />
      {children}
    </>
  );
}