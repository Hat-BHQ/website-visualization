import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MockAdapter from 'axios-mock-adapter';
import { afterEach, beforeEach, test, vi, expect } from 'vitest';
import { QueryClientProvider } from '@tanstack/react-query';

import { apiClient } from '@/api/http';
import { queryClient } from '@/app/queryClient';
import { AppRouter } from '@/app/router';
import { clearAuthSession, resetAuthStore, setAuthSession, setAuthSnapshot } from '@/auth/sessionStore';
import type { CurrentUser } from '@/types/auth';
import type { SyncJobResponse } from '@/types/hqa';

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
      permissions: [
        'hqa.dashboard.view',
        'hqa.ebay.view',
        'hqa.reverb.view',
        'hqa.etsy.view',
        'hqa.sync_history.view',
        'hqa.ebay.sync',
        'hqa.reverb.sync',
        'hqa.etsy.sync',
      ],
    },
  ],
};

const hqaViewer: CurrentUser = {
  id: '22222222-2222-2222-2222-222222222222',
  email: 'viewer.hqa@company.com',
  full_name: 'HQA Viewer',
  is_superadmin: false,
  modules: [
    {
      code: 'HQA',
      name: 'HQ Audio Marketplace',
      role: 'user',
      frontend_path: '/hqa',
      permissions: ['hqa.dashboard.view', 'hqa.ebay.view', 'hqa.reverb.view', 'hqa.etsy.view'],
    },
  ],
};

function renderApp(initialEntry: string) {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <AppRouter />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function syncJob(status: SyncJobResponse['status'], id = 'job-1'): SyncJobResponse {
  return {
    id,
    marketplace: 'ebay',
    trigger_type: 'manual',
    status,
    scheduled_for: null,
    started_at: null,
    completed_at: null,
    total_source_rows: 10,
    inserted_rows: 2,
    updated_rows: 3,
    unchanged_rows: 4,
    skipped_rows: 0,
    error_rows: 1,
    requested_by_user_id: null,
    error_summary: null,
    metadata_: null,
    created_at: '2026-01-01T00:00:00Z',
  };
}

beforeEach(() => {
  queryClient.clear();
  resetAuthStore();
  setAuthSnapshot({ isLoading: false });
});

afterEach(() => {
  queryClient.clear();
  clearAuthSession();
  vi.useRealTimers();
});

test('Dashboard gọi API thật', async () => {
  const mock = new MockAdapter(apiClient);
  setAuthSession({ user: hqaAdmin, accessToken: 'access-token', refreshToken: 'refresh-token' });

  mock.onGet('/api/hqa/dashboard').reply(200, {
    ebay: { active_listings: 10, new_today: 2, last_sync_at: '2026-01-01T00:00:00Z', sync_status: 'success' },
    reverb: { active_listings: 4, new_today: 1, last_sync_at: '2026-01-01T00:00:00Z', sync_status: 'success' },
    etsy: { active_listings: 8, new_today: 3, last_sync_at: '2026-01-01T00:00:00Z', sync_status: 'partial_success' },
  });
  mock.onGet('/api/hqa/sync-jobs').reply((config) => {
    if (config.params?.marketplace === 'ebay') return [200, [syncJob('success', 'job-ebay')]];
    if (config.params?.marketplace === 'reverb') return [200, []];
    if (config.params?.marketplace === 'etsy') return [200, []];
    return [200, []];
  });

  renderApp('/hqa/dashboard');

  expect(await screen.findByText('HQA Dashboard')).toBeInTheDocument();
  await waitFor(() => {
    expect(mock.history.get.some((request) => request.url === '/api/hqa/dashboard')).toBe(true);
  });

  mock.restore();
});

test('Filter và pagination gửi đúng query', async () => {
  const mock = new MockAdapter(apiClient);
  setAuthSession({ user: hqaAdmin, accessToken: 'access-token', refreshToken: 'refresh-token' });

  const capturedParams: Array<Record<string, unknown>> = [];
  mock.onGet('/api/hqa/ebay/listings').reply((config) => {
    capturedParams.push({ ...(config.params as Record<string, unknown>) });
    return [
      200,
      {
        items: [
          {
            id: 'listing-1',
            external_listing_id: 'ebay|1001',
            listing_title: 'Listing 1',
            listing_url: 'https://example.com/1',
            seller_name: 'Seller',
            shop_name: null,
            shop_id: null,
            published_at: null,
            listing_location: null,
            country_code: null,
            category_id: null,
            category_name: null,
            condition_id: null,
            condition_name: null,
            image_url: null,
            current_price: '100.00',
            shipping_price: '0.00',
            total_price: '100.00',
            currency: 'USD',
            quantity: null,
            listing_views: null,
            listing_status: 'active',
            status_reason: null,
            first_seen_at: '2026-01-01T00:00:00Z',
            last_seen_at: '2026-01-01T01:00:00Z',
            state_hash: 'hash',
          },
        ],
        page: Number(config.params?.page ?? 1),
        page_size: Number(config.params?.page_size ?? 20),
        total: 25,
        pages: 3,
      },
    ];
  });
  mock.onGet(/\/api\/hqa\/ebay\/listings\/.+/).reply(200, {
    id: 'listing-1',
    external_listing_id: 'ebay|1001',
    listing_title: 'Listing 1',
    listing_url: 'https://example.com/1',
    seller_name: 'Seller',
    shop_name: null,
    shop_id: null,
    published_at: null,
    listing_location: null,
    country_code: null,
    category_id: null,
    category_name: null,
    condition_id: null,
    condition_name: null,
    image_url: null,
    current_price: '100.00',
    shipping_price: '0.00',
    total_price: '100.00',
    currency: 'USD',
    quantity: null,
    listing_views: null,
    listing_status: 'active',
    status_reason: null,
    first_seen_at: '2026-01-01T00:00:00Z',
    last_seen_at: '2026-01-01T01:00:00Z',
    state_hash: 'hash',
    raw_payload: null,
    buying_options: null,
    etsy_data: null,
  });
  mock.onGet(/\/api\/hqa\/ebay\/listings\/.+\/history/).reply(200, []);

  const user = userEvent.setup();
  renderApp('/hqa/ebay');

  await screen.findByText('Listing 1');
  await user.clear(screen.getByLabelText('Từ khóa'));
  await user.type(screen.getByLabelText('Từ khóa'), 'Synth');
  await user.clear(screen.getByLabelText('Status'));
  await user.type(screen.getByLabelText('Status'), 'active');
  await user.selectOptions(screen.getByLabelText('Page size'), '50');
  await user.click(screen.getByRole('button', { name: 'Áp dụng filter' }));

  await waitFor(() => {
    expect(capturedParams.length).toBeGreaterThan(1);
  });

  await user.click(screen.getByRole('button', { name: '2' }));
  await waitFor(() => {
    expect(capturedParams.some((item) => item.page === 2)).toBe(true);
  });

  const appliedParams = capturedParams[capturedParams.length - 2];
  expect(appliedParams.q).toBe('Synth');
  expect(appliedParams.status).toBe('active');
  expect(appliedParams.page_size).toBe(50);

  mock.restore();
});

test('User không thấy nút sync hoạt động', async () => {
  const mock = new MockAdapter(apiClient);
  setAuthSession({ user: hqaViewer, accessToken: 'access-token', refreshToken: 'refresh-token' });

  mock.onGet('/api/hqa/dashboard').reply(200, {
    ebay: { active_listings: 3, new_today: 1, last_sync_at: null, sync_status: null },
    reverb: { active_listings: 2, new_today: 0, last_sync_at: null, sync_status: null },
    etsy: { active_listings: 1, new_today: 0, last_sync_at: null, sync_status: null },
  });

  renderApp('/hqa/dashboard');
  await screen.findByText('HQA Dashboard');

  expect(screen.queryByRole('button', { name: 'Đồng bộ eBay' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Đồng bộ tất cả' })).not.toBeInTheDocument();

  mock.restore();
});

test('Admin chạy sync và thấy trạng thái job', async () => {
  const mock = new MockAdapter(apiClient);
  setAuthSession({ user: hqaAdmin, accessToken: 'access-token', refreshToken: 'refresh-token' });

  let dashboardCalls = 0;
  let pollCalls = 0;

  mock.onGet('/api/hqa/dashboard').reply(() => {
    dashboardCalls += 1;
    return [
      200,
      {
        ebay: { active_listings: 10, new_today: 2, last_sync_at: '2026-01-01T00:00:00Z', sync_status: 'success' },
        reverb: { active_listings: 4, new_today: 1, last_sync_at: null, sync_status: null },
        etsy: { active_listings: 8, new_today: 3, last_sync_at: null, sync_status: null },
      },
    ];
  });

  mock.onGet('/api/hqa/sync-jobs').reply((config) => {
    if (config.params?.marketplace === 'ebay') return [200, [syncJob('success', 'job-old-ebay')]];
    return [200, []];
  });

  mock.onPost('/api/hqa/sync/ebay').reply(202, {
    job_id: 'job-1',
    status: 'queued',
    marketplace: 'ebay',
  });

  mock.onGet('/api/hqa/sync-jobs/job-1').reply(() => {
    pollCalls += 1;
    if (pollCalls === 1) {
      return [200, syncJob('queued', 'job-1')];
    }
    return [200, syncJob('success', 'job-1')];
  });

  const user = userEvent.setup();
  renderApp('/hqa/dashboard');

  const syncButton = await screen.findByRole('button', { name: 'Đồng bộ eBay' });
  await user.click(syncButton);

  expect(await screen.findByText(/job-1/)).toBeInTheDocument();

  await waitFor(() => {
    expect(pollCalls).toBeGreaterThan(1);
  }, { timeout: 7000 });
  expect(await screen.findByText(/đã hoàn tất/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(dashboardCalls).toBeGreaterThan(1);
  }, { timeout: 7000 });

  mock.restore();
});

test('API 403 chuyển sang trang Forbidden', async () => {
  const mock = new MockAdapter(apiClient);
  setAuthSession({ user: hqaAdmin, accessToken: 'access-token', refreshToken: 'refresh-token' });

  mock.onGet('/api/hqa/ebay/listings').reply(403, { detail: 'Forbidden' });

  renderApp('/hqa/ebay');

  await waitFor(() => {
    expect(screen.getByText('403')).toBeInTheDocument();
  }, { timeout: 4000 });

  mock.restore();
});
