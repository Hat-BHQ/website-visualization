import { loginApi, logoutApi, meApi } from '@/api/auth';
import { queryClient } from '@/app/queryClient';
import type { CurrentUser } from '@/types/auth';
import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  getSessionExpiresAt,
  setAuthError,
  setAuthSession,
  setLoading,
} from '@/auth/sessionStore';

export async function loadCurrentUser() {
  const accessToken = getAccessToken();
  const expiresAt = getSessionExpiresAt();

  if (!accessToken || !expiresAt) {
    setLoading(false);
    return null;
  }

  if (expiresAt <= Date.now()) {
    clearAuthSession();
    setAuthError('Phiên đăng nhập đã hết hạn.');
    return null;
  }

  try {
    const user = await meApi();

    setAuthSession({
      user,
      accessToken,
      refreshToken: getRefreshToken(),
      expiresAt,
    });

    return user;
  } catch {
    clearAuthSession();
    setAuthError('Phiên đăng nhập không còn hợp lệ.');
    return null;
  }
}

export async function login(email: string, password: string) {
  setLoading(true);

  try {
    const tokens = await loginApi(email, password);

    const expiresAt =
      Date.now() + tokens.expires_in * 1000;

    setAuthSession({
      user: null,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      expiresAt,
    });

    const user = await meApi();

    setAuthSession({
      user,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      expiresAt,
    });

    return user;
  } catch (error) {
    clearAuthSession();
    setAuthError('Email hoặc mật khẩu không đúng.');
    throw error;
  }
}

// export async function refreshSession() {
//   const refreshToken = getRefreshToken();
//   if (!refreshToken) {
//     throw new Error('Missing refresh token');
//   }

//   const tokens = await refreshApi(refreshToken);
//   setAuthSession({ user: null, accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
//   const user = await meApi();
//   setAuthSession({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
//   return { user, tokens };
// }

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
