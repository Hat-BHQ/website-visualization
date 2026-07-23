import { Link } from 'react-router-dom';

export function ForbiddenPage() {
  return (
    <div className="forbidden-state">
      <div style={{ maxWidth: '34rem' }}>
        <div className="surface" style={{ padding: '2rem', borderRadius: '28px' }}>
          <h1 style={{ marginTop: 0 }}>403</h1>
          <p style={{ color: 'var(--muted)' }}>Bạn không có quyền truy cập khu vực này.</p>
          <Link className="action-button" to="/modules">
            Quay lại chọn module
          </Link>
        </div>
      </div>
    </div>
  );
}
