import { PageHeader } from '@/components/PageHeader';
import { ModuleLayout } from '@/layouts/ModuleLayout';
import type { CurrentUser } from '@/types/auth';

export function SystemPage({ user }: { user: CurrentUser }) {
  return (
    <ModuleLayout moduleCode="SYSTEM" user={user} title="System Management" subtitle="Area dành cho superadmin." >
      <PageHeader title="System Management" subtitle="Chỉ superadmin mới truy cập được khu vực này." />
      <div className="grid-cards">
        <section className="module-card">
          <h3>Users</h3>
          <p style={{ color: 'var(--muted)' }}>Quản lý tài khoản, module membership và audit.</p>
        </section>
        <section className="module-card">
          <h3>Security</h3>
          <p style={{ color: 'var(--muted)' }}>Quản trị session, token và cấu hình quyền.</p>
        </section>
        <section className="module-card">
          <h3>Infrastructure</h3>
          <p style={{ color: 'var(--muted)' }}>Theo dõi trạng thái các service của HQ Portal.</p>
        </section>
      </div>
    </ModuleLayout>
  );
}
