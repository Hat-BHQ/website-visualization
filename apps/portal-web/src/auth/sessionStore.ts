import type { CurrentUser } from '@/types/auth';

type Listener = () => void;

export interface AuthSnapshot {
  user: CurrentUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
  isLoading: boolean;
  error: string | null;
}

interface StoredAuthSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

const SESSION_STORAGE_KEY = 'hq-portal-auth-session';

function isStoredAuthSession(
  value: unknown,
): value is StoredAuthSession {
  if (
    typeof value !== 'object' ||
    value === null
  ) {
    return false;
  }

  const session = value as Record<string, unknown>;

  return (
    typeof session.accessToken === 'string' &&
    typeof session.refreshToken === 'string' &&
    typeof session.expiresAt === 'number'
  );
}

function getSessionStorage() {
  if (typeof window === 'undefined') return null;

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}
function readStoredSession(): StoredAuthSession | null {
  const storage = getSessionStorage();

  if (!storage) {
    return null;
  }

  try {
    const rawValue = storage.getItem(
      SESSION_STORAGE_KEY,
    );

    if (!rawValue) {
      return null;
    }

    const value: unknown = JSON.parse(rawValue);

    if (!isStoredAuthSession(value)) {
      storage.removeItem(SESSION_STORAGE_KEY);
      return null;
    }

    if (value.expiresAt <= Date.now()) {
      storage.removeItem(SESSION_STORAGE_KEY);
      return null;
    }

    return {
      accessToken: value.accessToken,
      refreshToken: value.refreshToken,
      expiresAt: value.expiresAt,
    };
  } catch {
    storage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

function createInitialSnapshot(): AuthSnapshot {
  const storedSession = readStoredSession();

  return {
    user: null,
    accessToken: storedSession?.accessToken ?? null,
    refreshToken: storedSession?.refreshToken ?? null,
    expiresAt: storedSession?.expiresAt ?? null,
    isLoading: true,
    error: null,
  };
}

let snapshot = createInitialSnapshot();

function persistSession() {
  const storage = getSessionStorage();

  if (!storage) {
    return;
  }

  if (snapshot.accessToken && snapshot.refreshToken && snapshot.expiresAt) {
    const storedSession: StoredAuthSession = {
      accessToken: snapshot.accessToken,
      refreshToken: snapshot.refreshToken,
      expiresAt: snapshot.expiresAt,
    };

    storage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify(storedSession),
    );

    return;
  }

  storage.removeItem(SESSION_STORAGE_KEY);
}

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
  persistSession();
  notify();
}

export function setAuthSession(
  payload: Pick<
    AuthSnapshot,
    'user' | 'accessToken' | 'refreshToken'
  > & {
    expiresAt?: number | null;
  },
) {
  snapshot = {
    ...snapshot,
    ...payload,
    expiresAt: payload.expiresAt ?? snapshot.expiresAt,
    isLoading: false,
    error: null,
  };

  persistSession();
  notify();
}

export function clearAuthSession() {
  snapshot = {
    user: null,
    accessToken: null,
    refreshToken: null,
    expiresAt: null,
    isLoading: false,
    error: null,
  };

  persistSession();
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

export function getSessionExpiresAt() {
  return snapshot.expiresAt;
}

export function setSessionExpiredHandler(handler: (() => void) | null) {
  sessionExpiredHandler = handler;
}

export function triggerSessionExpired() {
  sessionExpiredHandler?.();
}

export function getIsAuthenticated() {
  return Boolean(
    snapshot.accessToken &&
    snapshot.user &&
    snapshot.expiresAt &&
    snapshot.expiresAt > Date.now(),
  );
}

export function resetAuthStore() {
  getSessionStorage()?.removeItem(SESSION_STORAGE_KEY);

  snapshot = {
    user: null,
    accessToken: null,
    refreshToken: null,
    expiresAt: null,
    isLoading: true,
    error: null,
  };

  notify();
}
