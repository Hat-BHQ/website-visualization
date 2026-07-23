import type { ReactNode } from 'react';

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '1.75rem' }}>{title}</h1>
        {subtitle ? <p style={{ margin: '0.35rem 0 0', color: 'var(--muted)' }}>{subtitle}</p> : null}
      </div>
      {actions ? <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>{actions}</div> : null}
    </div>
  );
}
