import type { ReactNode } from 'react';

export function ErrorState({ title, message, action }: { title: string; message: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      <div style={{ maxWidth: '34rem' }}>
        <div className="error-box">
          <strong>{title}</strong>
          <p style={{ margin: '0.55rem 0 0' }}>{message}</p>
        </div>
        {action ? <div style={{ marginTop: '1rem' }}>{action}</div> : null}
      </div>
    </div>
  );
}
