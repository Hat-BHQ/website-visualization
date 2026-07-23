import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

import { isForbiddenError } from '@/api/errors';
import {
  getMarketplaceListingDetail,
  getMarketplaceListingHistory,
  getMarketplaceListings,
} from '@/api/hqa';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingScreen } from '@/components/LoadingScreen';
import { PageHeader } from '@/components/PageHeader';
import { ModuleLayout } from '@/layouts/ModuleLayout';
import type { CurrentUser } from '@/types/auth';
import type { ListingListParams, Marketplace } from '@/types/hqa';

const defaultFilters: ListingListParams = {
  page: 1,
  page_size: 20,
  sort_by: 'last_seen_at',
  sort_order: 'desc',
};

function formatDateTime(value: string | null) {
  if (!value) return 'N/A';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('vi-VN');
}

function paginationItems(pages: number, currentPage: number) {
  if (pages <= 1) return [1];
  const start = Math.max(1, currentPage - 2);
  const end = Math.min(pages, start + 4);
  const result: number[] = [];
  for (let page = start; page <= end; page += 1) {
    result.push(page);
  }
  if (!result.includes(1)) result.unshift(1);
  if (!result.includes(pages)) result.push(pages);
  return [...new Set(result)];
}

export function HqaMarketplacePage({
  user,
  marketplace,
  title,
}: {
  user: CurrentUser;
  marketplace: Marketplace;
  title: string;
}) {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ListingListParams>(defaultFilters);
  const [form, setForm] = useState<ListingListParams>(defaultFilters);
  const [selectedListingId, setSelectedListingId] = useState<string | null>(null);

  const listingsQuery = useQuery({
    queryKey: ['hqa', 'listings', marketplace, filters],
    queryFn: () => getMarketplaceListings(marketplace, filters),
  });

  const listingDetailQuery = useQuery({
    queryKey: ['hqa', 'listing', marketplace, selectedListingId],
    queryFn: () => getMarketplaceListingDetail(marketplace, selectedListingId as string),
    enabled: Boolean(selectedListingId),
  });

  const listingHistoryQuery = useQuery({
    queryKey: ['hqa', 'listing-history', marketplace, selectedListingId],
    queryFn: () => getMarketplaceListingHistory(marketplace, selectedListingId as string),
    enabled: Boolean(selectedListingId),
  });

  useEffect(() => {
    const hasForbidden = [
      listingsQuery.error,
      listingDetailQuery.error,
      listingHistoryQuery.error,
    ].some((error) => isForbiddenError(error));

    if (hasForbidden) {
      navigate('/403', { replace: true });
    }
  }, [listingsQuery.error, listingDetailQuery.error, listingHistoryQuery.error, navigate]);

  const listingItems = listingsQuery.data?.items ?? [];
  const pages = listingsQuery.data?.pages ?? 0;
  const pageItems = useMemo(() => paginationItems(pages, filters.page), [filters.page, pages]);

  const applyFilters = () => {
    setFilters({ ...form, page: 1 });
    setSelectedListingId(null);
  };

  const resetFilters = () => {
    setForm(defaultFilters);
    setFilters(defaultFilters);
    setSelectedListingId(null);
  };

  return (
    <ModuleLayout moduleCode="HQA" user={user} title={`${title} Listings`} subtitle="Danh sách và lịch sử biến động listing">
      <PageHeader title={`${title} Listings`} subtitle="Kết nối dữ liệu thật từ HQA Service" />

      <section className="surface" style={{ padding: '1rem', borderRadius: '18px', marginBottom: '1rem' }}>
        <div className="grid-cards" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          <label className="field-stack">
            <span className="field-label">Từ khóa</span>
            <input value={form.q ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, q: event.target.value || undefined }))} placeholder="Tên listing" />
          </label>
          <label className="field-stack">
            <span className="field-label">Status</span>
            <input value={form.status ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, status: event.target.value || undefined }))} placeholder="active" />
          </label>
          <label className="field-stack">
            <span className="field-label">Category</span>
            <input value={form.category ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value || undefined }))} placeholder="Synths" />
          </label>
          <label className="field-stack">
            <span className="field-label">Condition</span>
            <input value={form.condition ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, condition: event.target.value || undefined }))} placeholder="Used" />
          </label>
          <label className="field-stack">
            <span className="field-label">Seller</span>
            <input value={form.seller ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, seller: event.target.value || undefined }))} placeholder="Shop" />
          </label>
          <label className="field-stack">
            <span className="field-label">Min price</span>
            <input value={form.min_price ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, min_price: event.target.value || undefined }))} placeholder="0" />
          </label>
          <label className="field-stack">
            <span className="field-label">Max price</span>
            <input value={form.max_price ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, max_price: event.target.value || undefined }))} placeholder="500" />
          </label>
          <label className="field-stack">
            <span className="field-label">Date from</span>
            <input type="date" value={form.date_from ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, date_from: event.target.value || undefined }))} />
          </label>
          <label className="field-stack">
            <span className="field-label">Date to</span>
            <input type="date" value={form.date_to ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, date_to: event.target.value || undefined }))} />
          </label>
          <label className="field-stack">
            <span className="field-label">Page size</span>
            <select value={form.page_size} onChange={(event) => setForm((prev) => ({ ...prev, page_size: Number(event.target.value) }))}>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
          <label className="field-stack">
            <span className="field-label">Sort by</span>
            <input value={form.sort_by ?? ''} onChange={(event) => setForm((prev) => ({ ...prev, sort_by: event.target.value || undefined }))} placeholder="last_seen_at" />
          </label>
          <label className="field-stack">
            <span className="field-label">Sort order</span>
            <select value={form.sort_order ?? 'desc'} onChange={(event) => setForm((prev) => ({ ...prev, sort_order: event.target.value as 'asc' | 'desc' }))}>
              <option value="desc">desc</option>
              <option value="asc">asc</option>
            </select>
          </label>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
          <button className="action-button" type="button" onClick={applyFilters}>Áp dụng filter</button>
          <button className="action-button secondary" type="button" onClick={resetFilters}>Reset filter</button>
        </div>
      </section>

      {listingsQuery.isLoading ? <LoadingScreen label="Đang tải listings..." /> : null}

      {listingsQuery.isError ? (
        <ErrorState
          title="Không thể tải danh sách listing"
          message="Vui lòng thử lại sau hoặc kiểm tra quyền truy cập module."
          action={<button className="action-button" type="button" onClick={() => void listingsQuery.refetch()}>Thử lại</button>}
        />
      ) : null}

      {!listingsQuery.isLoading && !listingsQuery.isError && listingItems.length === 0 ? (
        <EmptyState title="Không có dữ liệu" message="Không tìm thấy listing nào với điều kiện lọc hiện tại." />
      ) : null}

      {!listingsQuery.isLoading && !listingsQuery.isError && listingItems.length > 0 ? (
        <section className="surface" style={{ padding: '1rem', borderRadius: '18px', overflow: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '900px' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: '0.6rem' }}>Title</th>
                <th style={{ textAlign: 'left', padding: '0.6rem' }}>External ID</th>
                <th style={{ textAlign: 'left', padding: '0.6rem' }}>Seller</th>
                <th style={{ textAlign: 'left', padding: '0.6rem' }}>Price</th>
                <th style={{ textAlign: 'left', padding: '0.6rem' }}>Status</th>
                <th style={{ textAlign: 'left', padding: '0.6rem' }}>Last updated</th>
                <th style={{ textAlign: 'left', padding: '0.6rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {listingItems.map((item) => (
                <tr key={item.id} style={{ borderTop: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.65rem' }}>{item.listing_title}</td>
                  <td style={{ padding: '0.65rem' }}>{item.external_listing_id}</td>
                  <td style={{ padding: '0.65rem' }}>{item.seller_name ?? item.shop_name ?? 'N/A'}</td>
                  <td style={{ padding: '0.65rem' }}>{item.current_price ?? 'N/A'}</td>
                  <td style={{ padding: '0.65rem' }}>{item.listing_status}</td>
                  <td style={{ padding: '0.65rem' }}>{formatDateTime(item.last_seen_at)}</td>
                  <td style={{ padding: '0.65rem' }}>
                    <button className="action-button" type="button" style={{ minHeight: '2.2rem', padding: '0.45rem 0.8rem' }} onClick={() => setSelectedListingId(item.id)}>
                      Xem chi tiết
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            {pageItems.map((page) => (
              <button
                key={page}
                type="button"
                className="action-button"
                style={{
                  minHeight: '2.4rem',
                  padding: '0.35rem 0.65rem',
                  background: page === filters.page ? 'linear-gradient(135deg, var(--hqa), #6366f1)' : 'rgba(79, 70, 229, 0.16)',
                  color: page === filters.page ? 'white' : 'var(--text)',
                  boxShadow: 'none',
                }}
                onClick={() => {
                  setFilters((prev) => ({ ...prev, page }));
                }}
              >
                {page}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {selectedListingId ? (
        <section className="module-card" style={{ marginTop: '1rem' }}>
          <h3 style={{ marginTop: 0 }}>Listing detail</h3>
          {listingDetailQuery.isLoading ? <LoadingScreen label="Đang tải chi tiết listing..." /> : null}
          {listingDetailQuery.isError ? (
            <ErrorState title="Không thể tải chi tiết" message="Vui lòng thử lại." action={<button className="action-button" type="button" onClick={() => void listingDetailQuery.refetch()}>Thử lại</button>} />
          ) : null}
          {listingDetailQuery.data ? (
            <div className="grid-cards" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
              <div className="surface" style={{ padding: '0.9rem', borderRadius: '14px' }}>
                <strong>Title</strong>
                <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{listingDetailQuery.data.listing_title}</div>
              </div>
              <div className="surface" style={{ padding: '0.9rem', borderRadius: '14px' }}>
                <strong>Listing URL</strong>
                <div style={{ marginTop: '0.35rem' }}><a href={listingDetailQuery.data.listing_url} target="_blank" rel="noreferrer">{listingDetailQuery.data.listing_url}</a></div>
              </div>
              <div className="surface" style={{ padding: '0.9rem', borderRadius: '14px' }}>
                <strong>Last updated</strong>
                <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{formatDateTime(listingDetailQuery.data.last_seen_at)}</div>
              </div>
              <div className="surface" style={{ padding: '0.9rem', borderRadius: '14px' }}>
                <strong>State hash</strong>
                <div style={{ color: 'var(--muted)', marginTop: '0.35rem' }}>{listingDetailQuery.data.state_hash ?? 'N/A'}</div>
              </div>
            </div>
          ) : null}

          <h4 style={{ marginTop: '1.25rem', marginBottom: '0.75rem' }}>History</h4>
          {listingHistoryQuery.isLoading ? <LoadingScreen label="Đang tải history..." /> : null}
          {listingHistoryQuery.isError ? (
            <ErrorState title="Không thể tải lịch sử" message="Vui lòng thử lại." action={<button className="action-button" type="button" onClick={() => void listingHistoryQuery.refetch()}>Thử lại</button>} />
          ) : null}
          {listingHistoryQuery.data && listingHistoryQuery.data.length === 0 ? (
            <EmptyState title="Không có lịch sử" message="Listing này chưa có bản ghi snapshot." />
          ) : null}
          {listingHistoryQuery.data && listingHistoryQuery.data.length > 0 ? (
            <div className="surface" style={{ borderRadius: '14px', overflow: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '760px' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '0.6rem' }}>Observed at</th>
                    <th style={{ textAlign: 'left', padding: '0.6rem' }}>Price</th>
                    <th style={{ textAlign: 'left', padding: '0.6rem' }}>Status</th>
                    <th style={{ textAlign: 'left', padding: '0.6rem' }}>State hash</th>
                  </tr>
                </thead>
                <tbody>
                  {listingHistoryQuery.data.map((item) => (
                    <tr key={item.id} style={{ borderTop: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.65rem' }}>{formatDateTime(item.observed_at)}</td>
                      <td style={{ padding: '0.65rem' }}>{item.price ?? 'N/A'}</td>
                      <td style={{ padding: '0.65rem' }}>{item.listing_status ?? 'N/A'}</td>
                      <td style={{ padding: '0.65rem' }}>{item.state_hash}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      ) : null}
    </ModuleLayout>
  );
}
