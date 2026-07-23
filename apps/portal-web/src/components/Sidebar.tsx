import { Link, NavLink } from 'react-router-dom';

import type { CurrentUser } from '@/types/auth';

const hqaItems = [
  { label: 'Dashboard', to: '/hqa/dashboard' },
  { label: 'eBay', to: '/hqa/ebay' },
  { label: 'Reverb', to: '/hqa/reverb' },
  { label: 'Etsy', to: '/hqa/etsy' },
  { label: 'Quản lý người dùng', to: '/system' },
];

const hqsItems = [
  { label: 'Dashboard', to: '/hqs/dashboard' },
  { label: 'Yêu cầu dịch vụ', to: '/hqs/dashboard#requests' },
  { label: 'Báo cáo', to: '/hqs/dashboard#reports' },
  { label: 'Quản lý người dùng', to: '/system' },
];

function hasPermission(user: CurrentUser, permission: string) {
  return user.modules.some((module) => module.permissions.includes(permission));
}

export function Sidebar({ moduleCode, user }: { moduleCode: 'HQA' | 'HQS' | 'SYSTEM'; user: CurrentUser }) {
  const items = moduleCode === 'HQA'
    ? hqaItems.filter((item) => item.label !== 'Quản lý người dùng' || hasPermission(user, 'hqa.users.manage'))
    : moduleCode === 'HQS'
      ? hqsItems.filter((item) => item.label !== 'Quản lý người dùng' || hasPermission(user, 'hqs.users.manage'))
      : [];

  return (
    <aside className="sidebar">
      <Link className="hero-brand" to="/modules" style={{ marginBottom: '0.5rem' }}>
        <span className="brand-mark">HQ</span>
        <span>HQ Portal</span>
      </Link>

      <div className="surface" style={{ background: 'rgba(255, 255, 255, 0.06)', borderColor: 'rgba(255, 255, 255, 0.08)', color: 'white', padding: '1rem', borderRadius: '20px' }}>
        <strong style={{ display: 'block' }}>{user.full_name}</strong>
        <span style={{ color: 'rgba(255,255,255,0.72)', fontSize: '0.9rem' }}>{user.email}</span>
      </div>

      <nav>
        {items.map((item) => (
          <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
