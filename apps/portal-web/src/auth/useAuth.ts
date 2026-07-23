import { useSyncExternalStore } from 'react';

import { login, loadCurrentUser, logoutSession, refreshSession } from '@/auth/sessionActions';
import { clearAuthSession, getAuthSnapshot, subscribe } from '@/auth/sessionStore';

export function useAuth() {
  const snapshot = useSyncExternalStore(subscribe, getAuthSnapshot, getAuthSnapshot);

  return {
    ...snapshot,
    isAuthenticated: Boolean(snapshot.accessToken && snapshot.user),
    login,
    logout: logoutSession,
    refresh: refreshSession,
    loadCurrentUser,
    clear: clearAuthSession,
  };
}
