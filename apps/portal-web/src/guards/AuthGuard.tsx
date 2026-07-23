import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';

import { LoadingScreen } from '@/components/LoadingScreen';
import { useAuth } from '@/auth/useAuth';

export function AuthGuard({ children }: { children: ReactNode }) {
  const auth = useAuth();

  if (auth.isLoading) {
    return <LoadingScreen label="Đang kiểm tra phiên đăng nhập..." />;
  }

  if (!auth.isAuthenticated) {
    return <Navigate replace to="/login" />;
  }

  return children;
}
