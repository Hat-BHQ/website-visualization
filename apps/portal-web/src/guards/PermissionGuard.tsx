import { useAuth } from '@/auth/useAuth';
import type { ReactNode } from 'react';

export function PermissionGuard({ permission, children, fallback = null }: { permission: string; children: ReactNode; fallback?: ReactNode }) {
  const auth = useAuth();

  if (auth.isLoading) {
    return null;
  }

  const allowed = Boolean(
    auth.user?.is_superadmin || auth.user?.modules.some((module) => module.permissions.includes(permission)),
  );

  if (!allowed) {
    return fallback;
  }

  return children;
}
