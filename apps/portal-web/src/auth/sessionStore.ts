import type { CurrentUser } from '@/types/auth';

type Listener = () => void;

export interface AuthSnapshot {
  user: CurrentUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialSnapshot: AuthSnapshot = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isLoading: true,
  error: null,
};

let snapshot = initialSnapshot;
const listeners = new Set<Listener>();
let sessionExpiredHandler: (() => void) | null = null;

function notify() {
  listeners.forEach((listener) => listener());
}

export function subscribe(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getAuthSnapshot() {
  return snapshot;
}

export function setAuthSnapshot(partial: Partial<AuthSnapshot>) {
  snapshot = { ...snapshot, ...partial };
  notify();
}

export function setAuthSession(payload: Pick<AuthSnapshot, 'user' | 'accessToken' | 'refreshToken'>) {
  snapshot = {
    ...snapshot,
    ...payload,
    isLoading: false,
    error: null,
  };
  notify();
}

export function clearAuthSession() {
  snapshot = {
    user: null,
    accessToken: null,
    refreshToken: null,
    isLoading: false,
    error: null,
  };
  notify();
}

export function setLoading(isLoading: boolean) {
  snapshot = { ...snapshot, isLoading };
  notify();
}

export function setAuthError(error: string | null) {
  snapshot = { ...snapshot, error };
  notify();
}

export function getAccessToken() {
  return snapshot.accessToken;
}

export function getRefreshToken() {
  return snapshot.refreshToken;
}

export function setSessionExpiredHandler(handler: (() => void) | null) {
  sessionExpiredHandler = handler;
}

export function triggerSessionExpired() {
  sessionExpiredHandler?.();
}

export function getIsAuthenticated() {
  return Boolean(snapshot.accessToken && snapshot.user);
}

export function resetAuthStore() {
  snapshot = initialSnapshot;
  notify();
}
