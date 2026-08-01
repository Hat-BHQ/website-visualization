import {
  useCallback,
  useEffect,
  useRef,
  useSyncExternalStore,
} from 'react';

import { useNavigate } from 'react-router-dom';

import {
  loadCurrentUser,
  logoutSession,
} from '@/auth/sessionActions';

import {
  getAuthSnapshot,
  getIdleExpiresAt,
  setSessionExpiredHandler,
  subscribe,
  touchSessionActivity,
} from '@/auth/sessionStore';

const ACTIVITY_THROTTLE_MS = 10_000;

function AuthLifecycleBridge() {
  const navigate = useNavigate();

  const isExpiringRef = useRef(false);

  const authSnapshot =
    useSyncExternalStore(
      subscribe,
      getAuthSnapshot,
      getAuthSnapshot,
    );

  const expireSession = useCallback(() => {
    if (isExpiringRef.current) {
      return;
    }

    isExpiringRef.current = true;

    void logoutSession().finally(() => {
      navigate('/login', {
        replace: true,
      });
    });
  }, [navigate]);

  // Cho phép đăng nhập lại sau khi phiên trước hết hạn.
  useEffect(() => {
    if (authSnapshot.accessToken) {
      isExpiringRef.current = false;
    }
  }, [authSnapshot.accessToken]);

  useEffect(() => {
    setSessionExpiredHandler(
      expireSession,
    );

    return () => {
      setSessionExpiredHandler(null);
    };
  }, [expireSession]);

  useEffect(() => {
    void loadCurrentUser();
  }, []);

  /**
   * Theo dõi thao tác thật của người dùng.
   *
   * API chạy nền, polling và refresh token
   * không được tính là thao tác.
   */
  useEffect(() => {
    if (!authSnapshot.accessToken) {
      return undefined;
    }

    let lastActivityWrite = 0;

    const handleActivity = () => {
      const now = Date.now();

      const idleExpiresAt =
        getIdleExpiresAt();

      if (
        !idleExpiresAt ||
        idleExpiresAt <= now
      ) {
        expireSession();
        return;
      }

      // Không ghi sessionStorage liên tục khi mousemove.
      if (
        now - lastActivityWrite <
        ACTIVITY_THROTTLE_MS
      ) {
        return;
      }

      lastActivityWrite = now;

      touchSessionActivity();
    };

    const handleVisibilityChange = () => {
      if (
        document.visibilityState ===
        'visible'
      ) {
        handleActivity();
      }
    };

    window.addEventListener(
      'pointerdown',
      handleActivity,
    );

    window.addEventListener(
      'pointermove',
      handleActivity,
    );

    window.addEventListener(
      'keydown',
      handleActivity,
    );

    window.addEventListener(
      'scroll',
      handleActivity,
      {
        passive: true,
      },
    );

    window.addEventListener(
      'touchstart',
      handleActivity,
      {
        passive: true,
      },
    );

    window.addEventListener(
      'focus',
      handleActivity,
    );

    document.addEventListener(
      'input',
      handleActivity,
      true,
    );

    document.addEventListener(
      'change',
      handleActivity,
      true,
    );

    document.addEventListener(
      'visibilitychange',
      handleVisibilityChange,
    );

    return () => {
      window.removeEventListener(
        'pointerdown',
        handleActivity,
      );

      window.removeEventListener(
        'pointermove',
        handleActivity,
      );

      window.removeEventListener(
        'keydown',
        handleActivity,
      );

      window.removeEventListener(
        'scroll',
        handleActivity,
      );

      window.removeEventListener(
        'touchstart',
        handleActivity,
      );

      window.removeEventListener(
        'focus',
        handleActivity,
      );

      document.removeEventListener(
        'input',
        handleActivity,
        true,
      );

      document.removeEventListener(
        'change',
        handleActivity,
        true,
      );

      document.removeEventListener(
        'visibilitychange',
        handleVisibilityChange,
      );
    };
  }, [
    authSnapshot.accessToken,
    expireSession,
  ]);

  /**
   * Hẹn giờ đăng xuất dựa trên idleExpiresAt.
   */
  useEffect(() => {
    if (
      !authSnapshot.accessToken ||
      !authSnapshot.idleExpiresAt
    ) {
      return undefined;
    }

    const remainingTime =
      authSnapshot.idleExpiresAt -
      Date.now();

    if (remainingTime <= 0) {
      expireSession();
      return undefined;
    }

    const timeoutId =
      window.setTimeout(
        expireSession,
        remainingTime,
      );

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [
    authSnapshot.accessToken,
    authSnapshot.idleExpiresAt,
    expireSession,
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