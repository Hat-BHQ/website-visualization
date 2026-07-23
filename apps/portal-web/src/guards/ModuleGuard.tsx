import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';

import { LoadingScreen } from '@/components/LoadingScreen';
import { useAuth } from '@/auth/useAuth';

export function ModuleGuard({ moduleCode, children }: { moduleCode: string; children: ReactNode }) {
  const auth = useAuth();

  if (auth.isLoading) {
    return <LoadingScreen label="Đang tải quyền truy cập..." />;
  }

  const hasAccess = Boolean(auth.user?.is_superadmin || auth.user?.modules.some((module) => module.code === moduleCode));
  if (!hasAccess) {
    return <Navigate replace to="/403" />;
  }

  return children;
}
