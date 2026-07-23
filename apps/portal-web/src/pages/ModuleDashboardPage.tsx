import { PageHeader } from '@/components/PageHeader';
import { ModuleLayout } from '@/layouts/ModuleLayout';
import type { CurrentUser } from '@/types/auth';

export function ModuleDashboardPage({ moduleCode, user, title, subtitle }: { moduleCode: 'HQA' | 'HQS'; user: CurrentUser; title: string; subtitle: string }) {
  return (
    <ModuleLayout moduleCode={moduleCode} user={user} title={title} subtitle={subtitle}>
      <PageHeader title={title} subtitle={subtitle} />
      <div className="grid-cards">
        <section className="module-card">
          <h3>Overview</h3>
          <p style={{ color: 'var(--muted)' }}>Layout cơ bản của dashboard cho {moduleCode}.</p>
        </section>
        <section className="module-card">
          <h3>Activity</h3>
          <p style={{ color: 'var(--muted)' }}>Sẵn sàng ghép dữ liệu thật từ backend ở bước tiếp theo.</p>
        </section>
        <section className="module-card">
          <h3>Actions</h3>
          <p style={{ color: 'var(--muted)' }}>Các nút thao tác sẽ được bật theo permission từ backend.</p>
        </section>
      </div>
    </ModuleLayout>
  );
}
