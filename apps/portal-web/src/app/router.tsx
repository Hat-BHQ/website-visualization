import { Navigate, Route, Routes } from 'react-router-dom';

import { ForbiddenPage } from '@/components/ForbiddenPage';
import { AuthGuard } from '@/guards/AuthGuard';
import { GuestGuard } from '@/guards/GuestGuard';
import { ModuleGuard } from '@/guards/ModuleGuard';
import { SuperadminGuard } from '@/guards/SuperadminGuard';
import { HqaDashboardPage } from '@/pages/HqaDashboardPage';
import { HqaMarketplacePage } from '@/pages/HqaMarketplacePage';
import { LoginPage } from '@/pages/LoginPage';
import { ModuleSelectorPage } from '@/pages/ModuleSelectorPage';
import { ModuleDashboardPage } from '@/pages/ModuleDashboardPage';
import { SystemPage } from '@/pages/SystemPage';
import { useAuth } from '@/auth/useAuth';

function HomeRedirect() {
  const auth = useAuth();
  if (auth.isLoading) {
    return null;
  }
  return <Navigate replace to={auth.isAuthenticated ? '/modules' : '/login'} />;
}

function HqaRoute() {
  const auth = useAuth();
  if (!auth.user) return null;
  return <HqaDashboardPage user={auth.user} />;
}

function HqaEbayRoute() {
  const auth = useAuth();
  if (!auth.user) return null;
  return <HqaMarketplacePage user={auth.user} marketplace="ebay" title="eBay" />;
}

function HqaReverbRoute() {
  const auth = useAuth();
  if (!auth.user) return null;
  return <HqaMarketplacePage user={auth.user} marketplace="reverb" title="Reverb" />;
}

function HqaEtsyRoute() {
  const auth = useAuth();
  if (!auth.user) return null;
  return <HqaMarketplacePage user={auth.user} marketplace="etsy" title="Etsy" />;
}

function HqsRoute() {
  const auth = useAuth();
  if (!auth.user) return null;
  return <ModuleDashboardPage moduleCode="HQS" user={auth.user} title="HQS Dashboard" subtitle="Service operations overview." />;
}

function SystemRoute() {
  const auth = useAuth();
  if (!auth.user) return null;
  return <SystemPage user={auth.user} />;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<GuestGuard><LoginPage /></GuestGuard>} />
      <Route path="/modules" element={<AuthGuard><ModuleSelectorPage /></AuthGuard>} />
      <Route path="/hqa/dashboard" element={<AuthGuard><ModuleGuard moduleCode="HQA"><HqaRoute /></ModuleGuard></AuthGuard>} />
      <Route path="/hqa/ebay" element={<AuthGuard><ModuleGuard moduleCode="HQA"><HqaEbayRoute /></ModuleGuard></AuthGuard>} />
      <Route path="/hqa/reverb" element={<AuthGuard><ModuleGuard moduleCode="HQA"><HqaReverbRoute /></ModuleGuard></AuthGuard>} />
      <Route path="/hqa/etsy" element={<AuthGuard><ModuleGuard moduleCode="HQA"><HqaEtsyRoute /></ModuleGuard></AuthGuard>} />
      <Route path="/hqs/dashboard" element={<AuthGuard><ModuleGuard moduleCode="HQS"><HqsRoute /></ModuleGuard></AuthGuard>} />
      <Route path="/system" element={<AuthGuard><SuperadminGuard><SystemRoute /></SuperadminGuard></AuthGuard>} />
      <Route path="/403" element={<ForbiddenPage />} />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  );
}
