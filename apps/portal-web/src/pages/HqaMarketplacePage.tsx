import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ListingDetailModal } from '@/components/ListingDetailModal';
import { isForbiddenError } from '@/api/errors';
import {
  getMarketplaceFilterOptions,
  getMarketplaceListingDetail,
  getMarketplaceListingHistory,
  getMarketplaceListings,
} from '@/api/hqa';
import { canExportHqaMarketplace } from '@/auth/permissions';
import { ListingExportModal } from '@/components/ListingExportModal';
import {
  FacetMultiSelect,
} from '@/components/FacetMultiSelect';
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

  status: [],
  category: [],
  condition: [],
  seller: [],
  currency: [],

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
  const canExport =
    canExportHqaMarketplace(
      user,
      marketplace,
    );
  const [exportModalOpen, setExportModalOpen] =
    useState(false);
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ListingListParams>(defaultFilters);
  const [form, setForm] = useState<ListingListParams>(defaultFilters);
  const [selectedListingId, setSelectedListingId] = useState<string | null>(null);

  const listingsQuery = useQuery({
    queryKey: ['hqa', 'listings', marketplace, filters],
    queryFn: () => getMarketplaceListings(marketplace, filters),
  });

  const filterOptionsQuery = useQuery({
    queryKey: [
      'hqa',
      'listing-filter-options',
      marketplace,
      filters,
    ],
    queryFn: () =>
      getMarketplaceFilterOptions(
        marketplace,
        filters,
      ),
    staleTime: 60_000,
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
          <FacetMultiSelect
            label="Status"
            value={form.status ?? []}
            options={
              filterOptionsQuery.data?.status ?? []
            }
            searchable={false}
            onApply={(values) =>
              setForm((prev) => ({
                ...prev,
                status: values,
              }))
            }
          />

          <FacetMultiSelect
            label="Category"
            value={form.category ?? []}
            options={
              filterOptionsQuery.data?.category ?? []
            }
            onApply={(values) =>
              setForm((prev) => ({
                ...prev,
                category: values,
              }))
            }
          />

          <FacetMultiSelect
            label="Condition"
            value={form.condition ?? []}
            options={
              filterOptionsQuery.data?.condition ?? []
            }
            onApply={(values) =>
              setForm((prev) => ({
                ...prev,
                condition: values,
              }))
            }
          />

          <FacetMultiSelect
            label="Seller"
            value={form.seller ?? []}
            options={
              filterOptionsQuery.data?.seller ?? []
            }
            onApply={(values) =>
              setForm((prev) => ({
                ...prev,
                seller: values,
              }))
            }
          />

          <FacetMultiSelect
            label="Currency"
            value={form.currency ?? []}
            options={
              filterOptionsQuery.data?.currency ?? []
            }
            searchable={false}
            onApply={(values) =>
              setForm((prev) => ({
                ...prev,
                currency: values,
              }))
            }
          />
          <label className="field-stack">
            <span className="field-label">
              Min price
            </span>

            <input
              type="number"
              min="0"
              step="0.01"
              value={form.min_price ?? ''}
              placeholder={
                filterOptionsQuery.data
                  ?.price_range.min ?? '0'
              }
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  min_price:
                    event.target.value || undefined,
                }))
              }
            />
          </label>

          <label className="field-stack">
            <span className="field-label">
              Max price
            </span>

            <input
              type="number"
              min="0"
              step="0.01"
              value={form.max_price ?? ''}
              placeholder={
                filterOptionsQuery.data
                  ?.price_range.max ?? '500'
              }
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  max_price:
                    event.target.value || undefined,
                }))
              }
            />
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
            <span className="field-label">
              Sort by
            </span>

            <select
              value={form.sort_by ?? 'last_seen_at'}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  sort_by:
                    event.target.value as ListingListParams['sort_by'],
                }))
              }
            >
              <option value="last_seen_at">
                Last updated
              </option>

              <option value="published_at">
                Published date
              </option>

              <option value="status">
                Status
              </option>

              <option value="category">
                Category
              </option>

              <option value="condition">
                Condition
              </option>

              <option value="seller">
                Seller
              </option>

              <option value="price">
                Price
              </option>
            </select>
          </label>
          <label className="field-stack">
            <span className="field-label">Sort order</span>
            <select value={form.sort_order ?? 'desc'} onChange={(event) => setForm((prev) => ({ ...prev, sort_order: event.target.value as 'asc' | 'desc' }))}>
              <option value="desc">Giảm dần</option>
              <option value="asc"> Tăng dần</option>
            </select>
          </label>
        </div>

        <div className="filter-actions">
          <button
            className="action-button"
            type="button"
            onClick={applyFilters}
          >
            Áp dụng filter
          </button>

          <button
            className="action-button secondary"
            type="button"
            onClick={resetFilters}
          >
            Reset filter
          </button>

          {canExport ? (
            <button
              className="action-button export-button"
              type="button"
              onClick={() => {
                setExportModalOpen(true);
              }}
            >
              Xuất dữ liệu
            </button>
          ) : null}
        </div>
      </section>
      <div className="active-filters">
        {(filters.status ?? []).map((value) => (
          <button
            key={`status-${value}`}
            type="button"
            onClick={() => {
              const nextValues =
                (filters.status ?? []).filter(
                  (item) => item !== value,
                );

              setFilters((prev) => ({
                ...prev,
                status: nextValues,
                page: 1,
              }));

              setForm((prev) => ({
                ...prev,
                status: nextValues,
              }));
            }}
          >
            Status: {value} ×
          </button>
        ))}

        {(filters.category ?? []).map((value) => (
          <button
            key={`category-${value}`}
            type="button"
            onClick={() => {
              const nextValues =
                (filters.category ?? []).filter(
                  (item) => item !== value,
                );

              setFilters((prev) => ({
                ...prev,
                category: nextValues,
                page: 1,
              }));

              setForm((prev) => ({
                ...prev,
                category: nextValues,
              }));
            }}
          >
            Category: {value} ×
          </button>
        ))}
      </div>
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
        <section className="" style={{ padding: '1rem', borderRadius: '18px', overflow: 'auto', background: '#fff', boxShadow: '0 24px 60px rgba(15, 23, 42, 0.12)', }}>
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

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
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
      ) : null
      }

      {
        selectedListingId ? (
          <ListingDetailModal
            open={Boolean(selectedListingId)}
            detail={listingDetailQuery.data}
            history={listingHistoryQuery.data}
            detailLoading={listingDetailQuery.isLoading}
            historyLoading={listingHistoryQuery.isLoading}
            detailError={listingDetailQuery.isError}
            historyError={listingHistoryQuery.isError}
            onClose={() => {
              setSelectedListingId(null);
            }}
            onRetryDetail={() => {
              void listingDetailQuery.refetch();
            }}
            onRetryHistory={() => {
              void listingHistoryQuery.refetch();
            }}
          />
        ) : null
      }
      {canExport ? (
        <ListingExportModal
          open={exportModalOpen}
          marketplace={marketplace}
          filters={filters}
          onClose={() => {
            setExportModalOpen(false);
          }}
        />
      ) : null}
    </ModuleLayout >
  );
}
