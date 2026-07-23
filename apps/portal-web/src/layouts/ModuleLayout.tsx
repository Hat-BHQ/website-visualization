import { Sidebar } from '@/components/Sidebar';
import { Topbar } from '@/components/Topbar';
import type { CurrentUser } from '@/types/auth';
import type { ReactNode } from 'react';

export function ModuleLayout({ moduleCode, user, title, subtitle, children }: { moduleCode: 'HQA' | 'HQS' | 'SYSTEM'; user: CurrentUser; title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div className="main-shell">
      <Sidebar moduleCode={moduleCode} user={user} />
      <div className="content-shell">
        <Topbar title={title} subtitle={subtitle} />
        <main className="content-body">{children}</main>
      </div>
    </div>
  );
}
