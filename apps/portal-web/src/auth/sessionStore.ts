import type { CurrentUser } from '@/types/auth';

type Listener = () => void;

export const IDLE_TIMEOUT_MS = 15 * 60 * 1000;

export interface AuthSnapshot {
  user: CurrentUser | null;
  accessToken: string | null;
  refreshToken: string | null;

  // Thời điểm access token hết hạn.
  expiresAt: number | null;

  // Thời điểm đăng xuất nếu không có thao tác.
  idleExpiresAt: number | null;

  isLoading: boolean;
  error: string | null;
}



interface LegacyStoredAuthSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}
function isLegacyStoredAuthSession(
  value: unknown,
): value is LegacyStoredAuthSession {
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

const SESSION_STORAGE_KEY = 'hq-portal-auth-session';
interface StoredAuthSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  idleExpiresAt: number;
}
function getSessionStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

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
    typeof session.expiresAt === 'number' &&
    typeof session.idleExpiresAt === 'number'
  );
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
    const now = Date.now();

    /**
     * Phiên theo định dạng mới, đã có idleExpiresAt.
     */
    if (isStoredAuthSession(value)) {
      if (value.idleExpiresAt <= now) {
        storage.removeItem(SESSION_STORAGE_KEY);
        return null;
      }

      return value;
    }

    /**
     * Phiên theo định dạng cũ, chưa có idleExpiresAt.
     * Tự động chuyển sang định dạng mới và cho phép
     * tiếp tục hoạt động thêm 15 phút.
     */
    if (isLegacyStoredAuthSession(value)) {
      const migratedSession: StoredAuthSession = {
        accessToken: value.accessToken,
        refreshToken: value.refreshToken,
        expiresAt: value.expiresAt,
        idleExpiresAt: now + IDLE_TIMEOUT_MS,
      };

      storage.setItem(
        SESSION_STORAGE_KEY,
        JSON.stringify(migratedSession),
      );

      return migratedSession;
    }

    storage.removeItem(SESSION_STORAGE_KEY);
    return null;
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
    idleExpiresAt:
      storedSession?.idleExpiresAt ?? null,
    isLoading: true,
    error: null,
  };
}

let snapshot = createInitialSnapshot();

const listeners = new Set<Listener>();

let sessionExpiredHandler:
  | (() => void)
  | null = null;

function persistSession() {
  const storage = getSessionStorage();

  if (!storage) {
    return;
  }

  if (
    snapshot.accessToken &&
    snapshot.refreshToken &&
    snapshot.expiresAt &&
    snapshot.idleExpiresAt
  ) {
    const storedSession: StoredAuthSession = {
      accessToken: snapshot.accessToken,
      refreshToken: snapshot.refreshToken,
      expiresAt: snapshot.expiresAt,
      idleExpiresAt: snapshot.idleExpiresAt,
    };

    storage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify(storedSession),
    );

    return;
  }

  storage.removeItem(SESSION_STORAGE_KEY);
}

function notify() {
  listeners.forEach((listener) => listener());
}

export function subscribe(listener: Listener) {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

export function getAuthSnapshot() {
  return snapshot;
}

export function setAuthSnapshot(
  partial: Partial<AuthSnapshot>,
) {
  snapshot = {
    ...snapshot,
    ...partial,
  };

  persistSession();
  notify();
}

export function setAuthSession(
  payload: Pick<
    AuthSnapshot,
    'user' | 'accessToken' | 'refreshToken'
  > & {
    expiresAt: number | null;
    idleExpiresAt?: number | null;
  },
) {
  snapshot = {
    ...snapshot,
    ...payload,

    idleExpiresAt:
      payload.idleExpiresAt ??
      snapshot.idleExpiresAt,

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
    idleExpiresAt: null,
    isLoading: false,
    error: null,
  };

  persistSession();
  notify();
}

export function setLoading(isLoading: boolean) {
  snapshot = {
    ...snapshot,
    isLoading,
  };

  notify();
}

export function setAuthError(
  error: string | null,
) {
  snapshot = {
    ...snapshot,
    error,
  };

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

export function getIdleExpiresAt() {
  return snapshot.idleExpiresAt;
}

/**
 * Gia hạn thời gian không thao tác thêm 15 phút.
 *
 * Không được gọi nếu phiên đã hết hạn, tránh trường hợp
 * một thao tác sau 15 phút làm sống lại phiên cũ.
 */
export function touchSessionActivity() {
  const now = Date.now();

  if (
    !snapshot.accessToken ||
    !snapshot.idleExpiresAt ||
    snapshot.idleExpiresAt <= now
  ) {
    return false;
  }

  snapshot = {
    ...snapshot,
    idleExpiresAt: now + IDLE_TIMEOUT_MS,
  };

  persistSession();
  notify();

  return true;
}

export function setSessionExpiredHandler(
  handler: (() => void) | null,
) {
  sessionExpiredHandler = handler;
}

export function triggerSessionExpired() {
  sessionExpiredHandler?.();
}

export function getIsAuthenticated() {
  return Boolean(
    snapshot.accessToken &&
    snapshot.user &&
    snapshot.idleExpiresAt &&
    snapshot.idleExpiresAt > Date.now(),
  );
}

export function resetAuthStore() {
  getSessionStorage()?.removeItem(
    SESSION_STORAGE_KEY,
  );

  snapshot = {
    user: null,
    accessToken: null,
    refreshToken: null,
    expiresAt: null,
    idleExpiresAt: null,
    isLoading: true,
    error: null,
  };

  notify();
}