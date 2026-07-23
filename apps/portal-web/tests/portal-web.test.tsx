import { useEffect } from 'react';
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MockAdapter from 'axios-mock-adapter';
import { vi } from 'vitest';
import { QueryClientProvider } from '@tanstack/react-query';

import { apiClient } from '@/api/http';
import { queryClient } from '@/app/queryClient';
import { AppRouter } from '@/app/router';
import { ForbiddenPage } from '@/components/ForbiddenPage';
import { ModuleGuard } from '@/guards/ModuleGuard';
import { PermissionGuard } from '@/guards/PermissionGuard';
import { clearAuthSession, getAuthSnapshot, resetAuthStore, setAuthSession, setAuthSnapshot, setSessionExpiredHandler } from '@/auth/sessionStore';
import type { CurrentUser } from '@/types/auth';
import * as authApi from '@/api/auth';

vi.mock('@/api/auth', () => ({
  loginApi: vi.fn(),
  refreshApi: vi.fn(),
  logoutApi: vi.fn(),
  meApi: vi.fn(),
}));

const mockedAuthApi = vi.mocked(authApi);

const hqaAdmin: CurrentUser = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'admin.hqa@company.com',
  full_name: 'HQA Admin',
  is_superadmin: false,
  modules: [
    {
      code: 'HQA',
      name: 'HQ Audio Marketplace',
      role: 'admin',
      frontend_path: '/hqa',
      permissions: ['hqa.dashboard.view', 'hqa.ebay.view', 'hqa.ebay.sync', 'hqa.users.manage'],
    },
  ],
};

const hqaUser: CurrentUser = {
  id: '22222222-2222-2222-2222-222222222222',
  email: 'user.hqa@company.com',
  full_name: 'HQA User',
  is_superadmin: false,
  modules: [
    {
      code: 'HQA',
      name: 'HQ Audio Marketplace',
      role: 'user',
      frontend_path: '/hqa',
      permissions: ['hqa.dashboard.view', 'hqa.ebay.view'],
    },
  ],
};

const multiUser: CurrentUser = {
  id: '33333333-3333-3333-3333-333333333333',
  email: 'multi@company.com',
  full_name: 'Multi Module User',
  is_superadmin: false,
  modules: [
    {
      code: 'HQA',
      name: 'HQ Audio Marketplace',
      role: 'admin',
      frontend_path: '/hqa',
      permissions: ['hqa.dashboard.view'],
    },
    {
      code: 'HQS',
      name: 'HQ Services',
      role: 'user',
      frontend_path: '/hqs',
      permissions: ['hqs.dashboard.view'],
    },
  ],
};

const superadmin: CurrentUser = {
  id: '44444444-4444-4444-4444-444444444444',
  email: 'root@company.com',
  full_name: 'Superadmin',
  is_superadmin: true,
  modules: [
    {
      code: 'HQA',
      name: 'HQ Audio Marketplace',
      role: 'superadmin',
      frontend_path: '/hqa',
      permissions: ['hqa.dashboard.view', 'hqa.users.manage'],
    },
    {
      code: 'HQS',
      name: 'HQ Services',
      role: 'superadmin',
      frontend_path: '/hqs',
      permissions: ['hqs.dashboard.view', 'hqs.users.manage'],
    },
  ],
};

function renderApp(initialEntry = '/login') {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <AppRouter />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function ProtectedProbe() {
  const navigate = useNavigate();

  useEffect(() => {
    setSessionExpiredHandler(() => {
      clearAuthSession();
      navigate('/login', { replace: true });
    });
    return () => setSessionExpiredHandler(null);
  }, [navigate]);

  return (
    <button type="button" onClick={() => void apiClient.get('/api/protected').catch(() => undefined)}>
      Probe
    </button>
  );
}

beforeEach(() => {
  queryClient.clear();
  resetAuthStore();
  setAuthSnapshot({ isLoading: false });
});

afterEach(() => {
  queryClient.clear();
  clearAuthSession();
  setSessionExpiredHandler(null);
  vi.clearAllMocks();
});

test('login đúng chuyển đến /modules', async () => {
  mockedAuthApi.loginApi.mockResolvedValue({
    access_token: 'access-token',
    refresh_token: 'refresh-token',
    token_type: 'bearer',
    expires_in: 900,
  });
  mockedAuthApi.meApi.mockResolvedValue(hqaAdmin);

  const user = userEvent.setup();
  renderApp('/login');

  await user.type(screen.getByLabelText('Email'), 'admin.hqa@company.com');
  await user.type(screen.getByLabelText('Mật khẩu'), 'password');
  await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));

  expect(await screen.findByText('Chọn module')).toBeInTheDocument();
  expect(screen.getByText('HQ Audio Marketplace')).toBeInTheDocument();
});

test('login sai hiển thị lỗi', async () => {
  mockedAuthApi.loginApi.mockRejectedValue(new Error('Invalid credentials'));

  const user = userEvent.setup();
  renderApp('/login');

  await user.type(screen.getByLabelText('Email'), 'admin.hqa@company.com');
  await user.type(screen.getByLabelText('Mật khẩu'), 'wrong');
  await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));

  expect(await screen.findByText('Đăng nhập thất bại')).toBeInTheDocument();
});

test('HQA Admin chỉ thấy module HQA', () => {
  setAuthSession({ user: hqaAdmin, accessToken: 'access-token', refreshToken: 'refresh-token' });
  renderApp('/modules');

  expect(screen.getByText('HQ Audio Marketplace')).toBeInTheDocument();
  expect(screen.queryByText('HQ Services')).not.toBeInTheDocument();
});

test('Multi user thấy HQA và HQS', () => {
  setAuthSession({ user: multiUser, accessToken: 'access-token', refreshToken: 'refresh-token' });
  renderApp('/modules');

  expect(screen.getByText('HQ Audio Marketplace')).toBeInTheDocument();
  expect(screen.getByText('HQ Services')).toBeInTheDocument();
});

test('ModuleGuard chặn user không có module', async () => {
  setAuthSession({ user: hqaUser, accessToken: 'access-token', refreshToken: 'refresh-token' });

  render(
    <MemoryRouter initialEntries={['/hqs/dashboard']}>
      <Routes>
        <Route path="/hqs/dashboard" element={<ModuleGuard moduleCode="HQS"><div>Allowed</div></ModuleGuard>} />
        <Route path="/403" element={<ForbiddenPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText('403')).toBeInTheDocument();
});

test('PermissionGuard ẩn chức năng không có quyền', () => {
  setAuthSession({ user: hqaUser, accessToken: 'access-token', refreshToken: 'refresh-token' });

  render(
    <PermissionGuard permission="hqa.ebay.sync">
      <button type="button">Đồng bộ eBay</button>
    </PermissionGuard>,
  );

  expect(screen.queryByRole('button', { name: 'Đồng bộ eBay' })).not.toBeInTheDocument();
});

test('Superadmin thấy System Management', () => {
  setAuthSession({ user: superadmin, accessToken: 'access-token', refreshToken: 'refresh-token' });
  renderApp('/modules');

  expect(screen.getByText('System Management')).toBeInTheDocument();
});

test('Logout xóa auth state', async () => {
  mockedAuthApi.logoutApi.mockResolvedValue(undefined);
  setAuthSession({ user: hqaAdmin, accessToken: 'access-token', refreshToken: 'refresh-token' });

  const user = userEvent.setup();
  renderApp('/hqa/dashboard');

  await user.click(screen.getByRole('button', { name: 'Logout' }));

  expect(await screen.findByRole('heading', { name: 'Đăng nhập' })).toBeInTheDocument();
  expect(getAuthSnapshot().user).toBeNull();
});

test('Refresh token thất bại chuyển về login', async () => {
  const mockAdapter = new MockAdapter(apiClient);
  mockAdapter.onGet('/api/protected').reply(401);
  mockedAuthApi.refreshApi.mockRejectedValue(new Error('refresh failed'));
  setAuthSession({ user: hqaAdmin, accessToken: 'expired-access', refreshToken: 'refresh-token' });

  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={['/modules']}>
      <Routes>
        <Route path="/modules" element={<ProtectedProbe />} />
        <Route path="/login" element={<div>Đăng nhập</div>} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(screen.getByRole('button', { name: 'Probe' }));

  expect(await screen.findByText('Đăng nhập')).toBeInTheDocument();
  expect(getAuthSnapshot().user).toBeNull();

  mockAdapter.restore();
});
