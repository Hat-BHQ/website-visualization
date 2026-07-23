import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';

import { LoadingScreen } from '@/components/LoadingScreen';
import { useAuth } from '@/auth/useAuth';

export function SuperadminGuard({ children }: { children: ReactNode }) {
  const auth = useAuth();

  if (auth.isLoading) {
    return <LoadingScreen label="Đang kiểm tra quyền superadmin..." />;
  }

  if (!auth.user?.is_superadmin) {
    return <Navigate replace to="/403" />;
  }

  return children;
}
