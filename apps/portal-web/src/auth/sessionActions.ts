import {
  loginApi,
  logoutApi,
  meApi,
  refreshApi,
} from '@/api/auth';

import { queryClient } from '@/app/queryClient';

import {
  clearAuthSession,
  getAccessToken,
  getAuthSnapshot,
  getIdleExpiresAt,
  getRefreshToken,
  getSessionExpiresAt,
  IDLE_TIMEOUT_MS,
  setAuthError,
  setAuthSession,
  setLoading,
} from '@/auth/sessionStore';

import type { CurrentUser } from '@/types/auth';

let refreshPromise:
  | Promise<string | null>
  | null = null;

/**
 * Dùng một Promise chung để tránh nhiều request 401
 * cùng refresh token một lúc.
 */
export function refreshSession():
  Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken();
    const idleExpiresAt = getIdleExpiresAt();

    if (
      !refreshToken ||
      !idleExpiresAt ||
      idleExpiresAt <= Date.now()
    ) {
      clearAuthSession();
      return null;
    }

    const tokens = await refreshApi(
      refreshToken,
    );

    const currentSnapshot =
      getAuthSnapshot();

    const newAccessToken =
      tokens.access_token;

    const newRefreshToken =
      tokens.refresh_token || refreshToken;

    const newExpiresAt =
      Date.now() +
      tokens.expires_in * 1000;

    setAuthSession({
      user: currentSnapshot.user,
      accessToken: newAccessToken,
      refreshToken: newRefreshToken,
      expiresAt: newExpiresAt,

      // Refresh token không được tự gia hạn idle timeout.
      // Chỉ thao tác thật của người dùng mới gia hạn.
      idleExpiresAt,
    });

    return newAccessToken;
  })()
    .catch((error: unknown) => {
      clearAuthSession();
      throw error;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

export async function loadCurrentUser() {
  setLoading(true);

  const accessToken = getAccessToken();
  const refreshToken = getRefreshToken();
  const idleExpiresAt = getIdleExpiresAt();

  /**
   * Người dùng chưa đăng nhập hoặc không có phiên lưu.
   * Đây là trạng thái bình thường, không phải phiên hết hạn.
   */
  if (!accessToken && !refreshToken) {
    setAuthError(null);
    setLoading(false);
    return null;
  }

  /**
   * Có dữ liệu phiên nhưng thiếu refresh token hoặc idle timeout.
   * Xóa phiên lỗi nhưng không hiện thông báo hết hạn giả.
   */
  if (!refreshToken || !idleExpiresAt) {
    clearAuthSession();
    setAuthError(null);
    return null;
  }

  /**
   * Chỉ hiển thị thông báo khi thực sự đã quá 15 phút
   * không có thao tác.
   */
  if (idleExpiresAt <= Date.now()) {
    clearAuthSession();

    setAuthError(
      'Phiên đăng nhập đã hết hạn do không hoạt động.',
    );

    return null;
  }

  try {
    let currentAccessToken = accessToken;
    const expiresAt = getSessionExpiresAt();

    /**
     * Access token hết hạn nhưng người dùng vẫn còn
     * trong thời gian hoạt động thì refresh token.
     */
    if (
      !currentAccessToken ||
      !expiresAt ||
      expiresAt <= Date.now() + 5_000
    ) {
      currentAccessToken = await refreshSession();
    }

    if (!currentAccessToken) {
      throw new Error(
        'Không thể làm mới phiên đăng nhập.',
      );
    }

    const user = await meApi();

    const latestAccessToken = getAccessToken();
    const latestRefreshToken = getRefreshToken();
    const latestExpiresAt = getSessionExpiresAt();
    const latestIdleExpiresAt = getIdleExpiresAt();

    if (
      !latestAccessToken ||
      !latestRefreshToken ||
      !latestExpiresAt ||
      !latestIdleExpiresAt
    ) {
      throw new Error(
        'Thông tin phiên đăng nhập không hợp lệ.',
      );
    }

    setAuthSession({
      user,
      accessToken: latestAccessToken,
      refreshToken: latestRefreshToken,
      expiresAt: latestExpiresAt,
      idleExpiresAt: latestIdleExpiresAt,
    });

    return user;
  } catch {
    clearAuthSession();

    setAuthError(
      'Phiên đăng nhập không còn hợp lệ.',
    );

    return null;
  }
}

export async function login(
  email: string,
  password: string,
) {
  setAuthError(null);
  setLoading(true);

  try {
    const tokens = await loginApi(
      email,
      password,
    );

    const now = Date.now();

    const expiresAt =
      now + tokens.expires_in * 1000;

    const idleExpiresAt =
      now + IDLE_TIMEOUT_MS;

    setAuthSession({
      user: null,
      accessToken:
        tokens.access_token,
      refreshToken:
        tokens.refresh_token,
      expiresAt,
      idleExpiresAt,
    });

    const user = await meApi();

    setAuthSession({
      user,
      accessToken:
        tokens.access_token,
      refreshToken:
        tokens.refresh_token,
      expiresAt,
      idleExpiresAt,
    });

    return user;
  } catch (error) {
    clearAuthSession();

    setAuthError(
      'Email hoặc mật khẩu không đúng.',
    );

    throw error;
  }
}

export async function logoutSession() {
  const refreshToken =
    getRefreshToken();

  try {
    await logoutApi(refreshToken);
  } catch {
    // Vẫn xóa phiên local nếu API logout lỗi.
  } finally {
    clearAuthSession();
    queryClient.clear();
  }
}

export function setAuthenticatedUser(
  user: CurrentUser,
  accessToken: string,
  refreshToken: string,
  expiresAt: number,
  idleExpiresAt: number,
) {
  setAuthSession({
    user,
    accessToken,
    refreshToken,
    expiresAt,
    idleExpiresAt,
  });
}