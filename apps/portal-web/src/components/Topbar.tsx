import { Link } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '@/auth/useAuth';

export function Topbar({ title, subtitle }: { title: string; subtitle?: string }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const user = auth.user;
  const initials = user ? user.full_name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase() : 'HQ';

  return (
    <header className="topbar">
      <div className="topbar-title">
        <strong>{title}</strong>
        {subtitle ? <span style={{ color: 'var(--muted)', fontSize: '0.92rem' }}>{subtitle}</span> : null}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {user ? (
          <div className="user-chip">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="avatar">{initials}</div>
              <div style={{ lineHeight: 1.4 }}>
                <strong style={{ display: 'block' }}>{user.full_name}</strong>
                <span style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>{user.email}</span>
              </div>
            </div>
            <button
              className="action-button"
              type="button"
              style={{ minHeight: '2.7rem', padding: '0.6rem 0.95rem' }}
              onClick={async () => {
                await auth.logout();
                navigate('/login', { replace: true });
              }}
            >
              Logout
            </button>
          </div>
        ) : (
          <Link className="action-button" to="/login">
            Login
          </Link>
        )}
      </div>
    </header>
  );
}
