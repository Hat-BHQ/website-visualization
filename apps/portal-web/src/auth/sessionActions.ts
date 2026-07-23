import { loginApi, logoutApi, meApi, refreshApi } from '@/api/auth';
import { queryClient } from '@/app/queryClient';
import { clearAuthSession, getAccessToken, getRefreshToken, setAuthError, setAuthSession, setLoading } from '@/auth/sessionStore';
import type { CurrentUser } from '@/types/auth';

export async function loadCurrentUser() {
  const accessToken = getAccessToken();
  if (!accessToken) {
    setLoading(false);
    return null;
  }

  try {
    const user = await meApi();
    setAuthSession({ user, accessToken, refreshToken: getRefreshToken() });
    return user;
  } catch (error) {
    if (getRefreshToken()) {
      try {
        const refreshed = await refreshSession();
        return refreshed.user;
      } catch {
        clearAuthSession();
        setAuthError('Không thể tải phiên đăng nhập.');
        return null;
      }
    }

    clearAuthSession();
    setAuthError('Không thể tải phiên đăng nhập.');
    return null;
  }
}

export async function login(email: string, password: string) {
  setLoading(true);
  try {
    const tokens = await loginApi(email, password);
    setAuthSession({ user: null, accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    const user = await meApi();
    setAuthSession({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    return user;
  } catch (error) {
    clearAuthSession();
    setAuthError('Email hoặc mật khẩu không đúng.');
    throw error;
  }
}

export async function refreshSession() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('Missing refresh token');
  }

  const tokens = await refreshApi(refreshToken);
  setAuthSession({ user: null, accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
  const user = await meApi();
  setAuthSession({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
  return { user, tokens };
}

export async function logoutSession() {
  const refreshToken = getRefreshToken();
  try {
    await logoutApi(refreshToken);
  } catch {
    // Always clear local session.
  } finally {
    clearAuthSession();
    queryClient.clear();
  }
}

export function setAuthenticatedUser(user: CurrentUser, accessToken: string, refreshToken: string) {
  setAuthSession({ user, accessToken, refreshToken });
}
