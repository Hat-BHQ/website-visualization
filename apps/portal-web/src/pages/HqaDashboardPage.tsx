import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';

import { getConflictMessage, isForbiddenError } from '@/api/errors';
import { getHqaDashboard, getSyncJob, getSyncJobs, triggerSyncAll, triggerSyncMarketplace } from '@/api/hqa';
import { queryClient } from '@/app/queryClient';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingScreen } from '@/components/LoadingScreen';
import { PageHeader } from '@/components/PageHeader';
import { ModuleLayout } from '@/layouts/ModuleLayout';
import type { CurrentUser } from '@/types/auth';
import type { Marketplace, MarketplaceDashboard, SyncJobResponse } from '@/types/hqa';

const terminalStatuses = new Set(['success', 'partial_success', 'failed']);

function formatDateTime(value: string | null) {
  if (!value) return 'N/A';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('vi-VN');
}

function hasSyncPermission(user: CurrentUser, permission: string) {
  return Boolean(user.is_superadmin || user.modules.some((module) => module.permissions.includes(permission)));
}

function hasPermission(user: CurrentUser, permission: string) {
  return Boolean(user.is_superadmin || user.modules.some((module) => module.permissions.includes(permission)));
}

function MarketplacePanel({
  title,
  code,
  dashboard,
  latestJob,
  currentJob,
  canSync,
  syncing,
  onSync,
}: {
  title: string;
  code: Marketplace;
  dashboard: MarketplaceDashboard;
  latestJob: SyncJobResponse | null;
  currentJob: SyncJobResponse | null;
  canSync: boolean;
  syncing: boolean;
  onSync: (marketplace: Marketplace) => void;
}) {
  const displayJob = currentJob ?? latestJob;
  const status = currentJob?.status ?? dashboard.sync_status ?? 'idle';

  return (
    <section className="module-card" id={code}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
        <div>
          <h3 style={{ marginTop: 0 }}>{title}</h3>
          <p style={{ margin: 0, color: 'var(--muted)' }}>Active listings: {dashboard.active_listings} · New today: {dashboard.new_today}</p>
        </div>
        {canSync ? (
          <button className="action-button" type="button" disabled={syncing} onClick={() => onSync(code)}>
            {syncing ? 'Đang đồng bộ...' : `Đồng bộ ${title}`}
          </button>
        ) : null}
      </div>

      <div className="grid-cards" style={{ marginTop: '1rem' }}>
        <article className="surface" style={{ padding: '0.9rem 1rem', borderRadius: '16px' }}>
          <strong>Last sync</strong>
          <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{formatDateTime(dashboard.last_sync_at)}</div>
        </article>
        <article className="surface" style={{ padding: '0.9rem 1rem', borderRadius: '16px' }}>
          <strong>Sync status</strong>
          <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{status}</div>
        </article>
        <article className="surface" style={{ padding: '0.9rem 1rem', borderRadius: '16px' }}>
          <strong>Inserted</strong>
          <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{displayJob?.inserted_rows ?? 0}</div>
        </article>
        <article className="surface" style={{ padding: '0.9rem 1rem', borderRadius: '16px' }}>
          <strong>Updated</strong>
          <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{displayJob?.updated_rows ?? 0}</div>
        </article>
        <article className="surface" style={{ padding: '0.9rem 1rem', borderRadius: '16px' }}>
          <strong>Unchanged</strong>
          <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{displayJob?.unchanged_rows ?? 0}</div>
        </article>
        <article className="surface" style={{ padding: '0.9rem 1rem', borderRadius: '16px' }}>
          <strong>Error</strong>
          <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{displayJob?.error_rows ?? 0}</div>
        </article>
      </div>
    </section>
  );
}

export function HqaDashboardPage({ user }: { user: CurrentUser }) {
  const navigate = useNavigate();
  const [activeJobs, setActiveJobs] = useState<Partial<Record<Marketplace, string>>>({});
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  const canSync = useMemo(
    () => ({
      ebay: hasSyncPermission(user, 'hqa.ebay.sync'),
      reverb: hasSyncPermission(user, 'hqa.reverb.sync'),
      etsy: hasSyncPermission(user, 'hqa.etsy.sync'),
    }),
    [user],
  );
  const canViewSyncHistory = useMemo(() => hasPermission(user, 'hqa.sync_history.view'), [user]);

  const dashboardQuery = useQuery({
    queryKey: ['hqa', 'dashboard'],
    queryFn: getHqaDashboard,
  });

  const ebayJobsQuery = useQuery({
    queryKey: ['hqa', 'sync-jobs', 'ebay'],
    queryFn: () => getSyncJobs('ebay'),
    enabled: canViewSyncHistory,
  });

  const reverbJobsQuery = useQuery({
    queryKey: ['hqa', 'sync-jobs', 'reverb'],
    queryFn: () => getSyncJobs('reverb'),
    enabled: canViewSyncHistory,
  });

  const etsyJobsQuery = useQuery({
    queryKey: ['hqa', 'sync-jobs', 'etsy'],
    queryFn: () => getSyncJobs('etsy'),
    enabled: canViewSyncHistory,
  });

  const ebayPollingQuery = useQuery({
    queryKey: ['hqa', 'sync-job', activeJobs.ebay ?? 'idle-ebay'],
    queryFn: () => getSyncJob(activeJobs.ebay as string),
    enabled: Boolean(activeJobs.ebay),
    refetchInterval: (query) => {
      const status = (query.state.data as SyncJobResponse | undefined)?.status;
      if (status && terminalStatuses.has(status)) return false;
      return 2500;
    },
  });

  const reverbPollingQuery = useQuery({
    queryKey: ['hqa', 'sync-job', activeJobs.reverb ?? 'idle-reverb'],
    queryFn: () => getSyncJob(activeJobs.reverb as string),
    enabled: Boolean(activeJobs.reverb),
    refetchInterval: (query) => {
      const status = (query.state.data as SyncJobResponse | undefined)?.status;
      if (status && terminalStatuses.has(status)) return false;
      return 2500;
    },
  });

  const etsyPollingQuery = useQuery({
    queryKey: ['hqa', 'sync-job', activeJobs.etsy ?? 'idle-etsy'],
    queryFn: () => getSyncJob(activeJobs.etsy as string),
    enabled: Boolean(activeJobs.etsy),
    refetchInterval: (query) => {
      const status = (query.state.data as SyncJobResponse | undefined)?.status;
      if (status && terminalStatuses.has(status)) return false;
      return 2500;
    },
  });

  const singleSyncMutation = useMutation({
    mutationFn: triggerSyncMarketplace,
    onSuccess: (response) => {
      setSyncNotice(`Job ${response.job_id} đã vào queue cho ${response.marketplace}.`);
      setActiveJobs((prev) => ({ ...prev, [response.marketplace]: response.job_id }));
      void queryClient.invalidateQueries({ queryKey: ['hqa', 'sync-jobs', response.marketplace] });
    },
    onError: (error) => {
      if (isForbiddenError(error)) {
        navigate('/403', { replace: true });
        return;
      }
      setSyncNotice(getConflictMessage(error) ?? 'Không thể khởi chạy sync marketplace.');
    },
  });

  const batchSyncMutation = useMutation({
    mutationFn: triggerSyncAll,
    onSuccess: (response) => {
      if (response.items.length === 0) {
        setSyncNotice('Không có marketplace khả dụng để đồng bộ.');
        return;
      }
      setSyncNotice(`Đã đưa ${response.items.length} job vào queue.`);
      setActiveJobs((prev) => {
        const next = { ...prev };
        for (const item of response.items) {
          next[item.marketplace] = item.job_id;
        }
        return next;
      });
      void queryClient.invalidateQueries({ queryKey: ['hqa', 'sync-jobs'] });
    },
    onError: (error) => {
      if (isForbiddenError(error)) {
        navigate('/403', { replace: true });
        return;
      }
      setSyncNotice(getConflictMessage(error) ?? 'Không thể khởi chạy đồng bộ tất cả.');
    },
  });

  useEffect(() => {
    const errors = [
      dashboardQuery.error,
      canViewSyncHistory ? ebayJobsQuery.error : null,
      canViewSyncHistory ? reverbJobsQuery.error : null,
      canViewSyncHistory ? etsyJobsQuery.error : null,
      ebayPollingQuery.error,
      reverbPollingQuery.error,
      etsyPollingQuery.error,
    ];
    if (errors.some((error) => isForbiddenError(error))) {
      navigate('/403', { replace: true });
    }
  }, [
    dashboardQuery.error,
    ebayJobsQuery.error,
    reverbJobsQuery.error,
    etsyJobsQuery.error,
    ebayPollingQuery.error,
    reverbPollingQuery.error,
    etsyPollingQuery.error,
    navigate,
  ]);

  useEffect(() => {
    const entries: Array<[Marketplace, string | undefined, SyncJobResponse | undefined]> = [
      ['ebay', activeJobs.ebay, ebayPollingQuery.data],
      ['reverb', activeJobs.reverb, reverbPollingQuery.data],
      ['etsy', activeJobs.etsy, etsyPollingQuery.data],
    ];

    let hasCompletion = false;
    for (const [marketplace, jobId, job] of entries) {
      if (!jobId || !job || !terminalStatuses.has(job.status)) {
        continue;
      }
      hasCompletion = true;
      setActiveJobs((prev) => {
        if (prev[marketplace] !== jobId) {
          return prev;
        }
        const next = { ...prev };
        delete next[marketplace];
        return next;
      });
      setSyncNotice(`Job ${jobId} (${marketplace}) đã hoàn tất với trạng thái ${job.status}.`);
    }

    if (hasCompletion) {
      void queryClient.invalidateQueries({ queryKey: ['hqa'] });
    }
  }, [
    activeJobs.ebay,
    activeJobs.reverb,
    activeJobs.etsy,
    ebayPollingQuery.data,
    reverbPollingQuery.data,
    etsyPollingQuery.data,
  ]);

  if (dashboardQuery.isLoading) {
    return (
      <ModuleLayout moduleCode="HQA" user={user} title="HQA Dashboard" subtitle="Marketplace overview">
        <LoadingScreen label="Đang tải dashboard HQA..." />
      </ModuleLayout>
    );
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return (
      <ModuleLayout moduleCode="HQA" user={user} title="HQA Dashboard" subtitle="Marketplace overview">
        <ErrorState
          title="Không thể tải dashboard"
          message="Vui lòng thử lại sau hoặc kiểm tra kết nối HQA service."
          action={
            <button className="action-button" type="button" onClick={() => void dashboardQuery.refetch()}>
              Tải lại
            </button>
          }
        />
      </ModuleLayout>
    );
  }

  const latestEbayJob = canViewSyncHistory ? (ebayJobsQuery.data?.[0] ?? null) : null;
  const latestReverbJob = canViewSyncHistory ? (reverbJobsQuery.data?.[0] ?? null) : null;
  const latestEtsyJob = canViewSyncHistory ? (etsyJobsQuery.data?.[0] ?? null) : null;

  const canSyncAny = canSync.ebay || canSync.reverb || canSync.etsy;
  const anyMarketplaceRunning = Boolean(activeJobs.ebay || activeJobs.reverb || activeJobs.etsy);

  return (
    <ModuleLayout moduleCode="HQA" user={user} title="HQA Dashboard" subtitle="Marketplace overview and sync control">
      <PageHeader
        title="HQA Dashboard"
        subtitle="Theo dõi và đồng bộ riêng cho từng marketplace"
        actions={
          canSyncAny ? (
            <button
              className="action-button secondary"
              type="button"
              disabled={batchSyncMutation.isPending || anyMarketplaceRunning}
              onClick={() => void batchSyncMutation.mutateAsync()}
            >
              {batchSyncMutation.isPending ? 'Đang gửi yêu cầu...' : 'Đồng bộ tất cả'}
            </button>
          ) : null
        }
      />

      {syncNotice ? (
        <div className="notice" style={{ marginBottom: '1rem' }}>{syncNotice}</div>
      ) : null}

      <div className="grid-cards" style={{ gridTemplateColumns: '1fr', gap: '1rem' }}>
        <MarketplacePanel
          title="eBay"
          code="ebay"
          dashboard={dashboardQuery.data.ebay}
          latestJob={latestEbayJob}
          currentJob={ebayPollingQuery.data ?? (activeJobs.ebay ? ({ status: 'queued' } as SyncJobResponse) : null)}
          canSync={canSync.ebay}
          syncing={singleSyncMutation.isPending || Boolean(activeJobs.ebay)}
          onSync={(marketplace) => void singleSyncMutation.mutateAsync(marketplace)}
        />
        <MarketplacePanel
          title="Reverb"
          code="reverb"
          dashboard={dashboardQuery.data.reverb}
          latestJob={latestReverbJob}
          currentJob={reverbPollingQuery.data ?? (activeJobs.reverb ? ({ status: 'queued' } as SyncJobResponse) : null)}
          canSync={canSync.reverb}
          syncing={singleSyncMutation.isPending || Boolean(activeJobs.reverb)}
          onSync={(marketplace) => void singleSyncMutation.mutateAsync(marketplace)}
        />
        <MarketplacePanel
          title="Etsy"
          code="etsy"
          dashboard={dashboardQuery.data.etsy}
          latestJob={latestEtsyJob}
          currentJob={etsyPollingQuery.data ?? (activeJobs.etsy ? ({ status: 'queued' } as SyncJobResponse) : null)}
          canSync={canSync.etsy}
          syncing={singleSyncMutation.isPending || Boolean(activeJobs.etsy)}
          onSync={(marketplace) => void singleSyncMutation.mutateAsync(marketplace)}
        />
      </div>

      {!canSyncAny ? (
        <EmptyState
          title="Bạn không có quyền đồng bộ"
          message="Tài khoản hiện tại chỉ có quyền xem dữ liệu. Liên hệ quản trị viên để được cấp quyền hqa.*.sync nếu cần thao tác đồng bộ."
        />
      ) : null}
    </ModuleLayout>
  );
}
