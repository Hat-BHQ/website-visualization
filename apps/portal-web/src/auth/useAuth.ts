import { useSyncExternalStore } from 'react';

import {
  login,
  loadCurrentUser,
  logoutSession,
} from '@/auth/sessionActions';

import {
  clearAuthSession,
  getAuthSnapshot,
  subscribe,
} from '@/auth/sessionStore';

export function useAuth() {
  const snapshot = useSyncExternalStore(
    subscribe,
    getAuthSnapshot,
    getAuthSnapshot,
  );

  return {
    ...snapshot,

    isAuthenticated: Boolean(
      snapshot.accessToken &&
      snapshot.user &&
      snapshot.expiresAt &&
      snapshot.expiresAt > Date.now(),
    ),

    login,
    logout: logoutSession,
    loadCurrentUser,
    clear: clearAuthSession,
  };
}