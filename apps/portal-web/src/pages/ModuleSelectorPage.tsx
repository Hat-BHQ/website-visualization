import { Link } from 'react-router-dom';

import { EmptyState } from '@/components/EmptyState';
import { ModuleCard } from '@/components/ModuleCard';
import { PageHeader } from '@/components/PageHeader';
import { useAuth } from '@/auth/useAuth';

function getDescription(code: string) {
  if (code === 'HQA') return 'Marketplace operations for eBay, Reverb, and Etsy.';
  if (code === 'HQS') return 'Service dashboard and operational workspace.';
  return 'System management and admin controls.';
}

export function ModuleSelectorPage() {
  const auth = useAuth();
  const modules = auth.user?.modules ?? [];
  const cards = [...modules];

  if (auth.user?.is_superadmin) {
    cards.push({
      code: 'SYSTEM',
      name: 'System Management',
      role: 'superadmin',
      frontend_path: '/system',
      permissions: [],
    });
  }

  if (!auth.user) {
    return null;
  }

  if (cards.length === 0) {
    return (
      <EmptyState
        title="Không có module nào được cấp"
        message="Backend hiện chưa gán module cho tài khoản này. Hãy liên hệ quản trị viên để được cấp quyền truy cập phù hợp."
        action={<Link className="action-button" to="/login">Quay lại đăng nhập</Link>}
      />
    );
  }

  return (
    <div className="page" style={{ paddingTop: '2rem', paddingBottom: '2rem' }}>
      <PageHeader title="Chọn module" subtitle="Chỉ hiển thị các module được backend trả về cho tài khoản hiện tại." />
      <div className="grid-cards">
        {cards.map((module) => (
          <ModuleCard
            key={module.code}
            module={module}
            description={getDescription(module.code)}
            actionLabel={module.code === 'SYSTEM' ? 'Mở system' : 'Mở module'}
            actionPath={module.code === 'SYSTEM' ? '/system' : `${module.frontend_path}/dashboard`}
          />
        ))}
      </div>
    </div>
  );
}
