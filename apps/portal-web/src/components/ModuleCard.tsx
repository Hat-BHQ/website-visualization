import { Link } from 'react-router-dom';

import type { UserModule } from '@/types/auth';

const colorByCode: Record<string, string> = {
  HQA: 'var(--hqa)',
  HQS: 'var(--hqs)',
};

export function ModuleCard({ module, description, actionLabel = 'Mở module', actionPath }: { module: UserModule | { code: string; name: string; role: string; frontend_path: string; permissions: string[] }; description: string; actionLabel?: string; actionPath: string }) {
  const accent = colorByCode[module.code] ?? 'var(--hqa)';

  return (
    <article className="module-card" style={{ ['--module-color' as string]: accent }}>
      <div className="module-badge">{module.code}</div>
      <h3 style={{ marginBottom: '0.3rem' }}>{module.name}</h3>
      <p style={{ marginTop: 0, color: 'var(--muted)', lineHeight: 1.7 }}>{description}</p>
      <div className="module-meta">
        <span className="tag">Role: {module.role}</span>
        <span className="tag">{module.permissions.length} quyền</span>
      </div>
      <Link className="action-button" to={actionPath} style={{ background: accent }}>
        {actionLabel}
      </Link>
    </article>
  );
}
