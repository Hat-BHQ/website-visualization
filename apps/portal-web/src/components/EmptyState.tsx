import type { ReactNode } from 'react';

export function EmptyState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      <div style={{ maxWidth: '34rem' }}>
        <div className="surface" style={{ padding: '2rem', borderRadius: '28px' }}>
          <h2 style={{ marginTop: 0 }}>{title}</h2>
          <p style={{ color: 'var(--muted)', lineHeight: 1.7 }}>{message}</p>
          {action ? <div style={{ marginTop: '1rem' }}>{action}</div> : null}
        </div>
      </div>
    </div>
  );
}
