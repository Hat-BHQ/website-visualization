import { useAuth } from '@/auth/useAuth';

export function UserMenu() {
  const auth = useAuth();
  if (!auth.user) {
    return null;
  }

  return (
    <div className="user-chip">
      <div className="avatar">{auth.user.full_name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}</div>
      <div style={{ lineHeight: 1.35 }}>
        <strong style={{ display: 'block' }}>{auth.user.full_name}</strong>
        <span style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>{auth.user.email}</span>
      </div>
    </div>
  );
}
