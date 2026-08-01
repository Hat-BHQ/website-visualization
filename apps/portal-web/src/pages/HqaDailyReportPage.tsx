import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  useQuery,
} from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import {
  getMarketplaceDailyReport,
  getMarketplaceListingDetail,
  getMarketplaceListingHistory,
} from '@/api/hqa';
import { isForbiddenError } from '@/api/errors';

import {
  MarketplaceTabs,
} from '@/components/MarketplaceTabs';
import {
  LoadingScreen,
} from '@/components/LoadingScreen';
import {
  ErrorState,
} from '@/components/ErrorState';
import {
  EmptyState,
} from '@/components/EmptyState';
import {
  PageHeader,
} from '@/components/PageHeader';
import {
  FacetMultiSelect,
} from '@/components/FacetMultiSelect';
import {
  ListingDetailModal,
} from '@/components/ListingDetailModal';
import {
  ModuleLayout,
} from '@/layouts/ModuleLayout';

import type {
  CurrentUser,
} from '@/types/auth';
import type {
  DailyReportParams,
  Marketplace,
} from '@/types/hqa';


function formatDateTime(
  value: string | null,
) {
  if (!value) {
    return 'N/A';
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString('vi-VN');
}


function formatPrice(
  value: string | null,
  currency: string | null,
) {
  if (!value) {
    return 'N/A';
  }

  const numberValue = Number(value);

  if (Number.isNaN(numberValue)) {
    return value;
  }

  return new Intl.NumberFormat(
    'en-US',
    {
      maximumFractionDigits: 2,
    },
  ).format(numberValue)
    + (currency ? ` ${currency}` : '');
}


function paginationItems(
  pages: number,
  currentPage: number,
) {
  if (pages <= 1) {
    return [1];
  }

  const start = Math.max(1, currentPage - 2);
  const end = Math.min(pages, start + 4);
  const result: number[] = [];

  for (let page = start; page <= end; page += 1) {
    result.push(page);
  }

  if (!result.includes(1)) {
    result.unshift(1);
  }

  if (!result.includes(pages)) {
    result.push(pages);
  }

  return [...new Set(result)];
}


const initialFilters: DailyReportParams = {
  // Omit date on first load. The backend resolves the newest available report date.
  date: undefined,
  status: [],
  table: 'all',
  sort: 'last_updated_desc',
  page: 1,
  page_size: 20,
};


export function HqaDailyReportPage({
  user,
  marketplace,
  title,
}: {
  user: CurrentUser;
  marketplace: Marketplace;
  title: string;
}) {
  const navigate = useNavigate();

  const [form, setForm] =
    useState<DailyReportParams>({
      ...initialFilters,
    });

  const [filters, setFilters] =
    useState<DailyReportParams>({
      ...initialFilters,
    });

  const [selectedListingId, setSelectedListingId] =
    useState<string | null>(null);

  const reportQuery = useQuery({
    queryKey: [
      'hqa',
      'daily-report',
      marketplace,
      filters,
    ],
    queryFn: () =>
      getMarketplaceDailyReport(
        marketplace,
        filters,
      ),
  });

  const listingDetailQuery = useQuery({
    queryKey: [
      'hqa',
      'listing',
      marketplace,
      selectedListingId,
    ],
    queryFn: () =>
      getMarketplaceListingDetail(
        marketplace,
        selectedListingId as string,
      ),
    enabled: Boolean(selectedListingId),
  });

  const listingHistoryQuery = useQuery({
    queryKey: [
      'hqa',
      'listing-history',
      marketplace,
      selectedListingId,
    ],
    queryFn: () =>
      getMarketplaceListingHistory(
        marketplace,
        selectedListingId as string,
      ),
    enabled: Boolean(selectedListingId),
  });

  useEffect(() => {
    const resolvedDate =
      reportQuery.data?.selected_date;

    if (!resolvedDate) {
      return;
    }

    setForm((current) => {
      if (current.date) {
        return current;
      }

      return {
        ...current,
        date: resolvedDate,
      };
    });
  }, [reportQuery.data?.selected_date]);

  useEffect(() => {
    const hasForbidden = [
      reportQuery.error,
      listingDetailQuery.error,
      listingHistoryQuery.error,
    ].some((error) => isForbiddenError(error));

    if (hasForbidden) {
      navigate('/403', {
        replace: true,
      });
    }
  }, [
    reportQuery.error,
    listingDetailQuery.error,
    listingHistoryQuery.error,
    navigate,
  ]);

  const tableOptions = useMemo(
    () =>
      reportQuery.data?.table_counts
      ?? [
        {
          key: 'all' as const,
          label: 'All listings',
          count: 0,
        },
      ],
    [reportQuery.data?.table_counts],
  );

  const pages = reportQuery.data?.pages ?? 0;
  const pageItems = useMemo(
    () => paginationItems(pages, filters.page),
    [filters.page, pages],
  );

  const applyFilters = () => {
    setFilters({
      ...form,
      page: 1,
    });
    setSelectedListingId(null);
  };

  const resetFilters = () => {
    const resetValue: DailyReportParams = {
      ...initialFilters,
      status: [],
    };

    setForm(resetValue);
    setFilters(resetValue);
    setSelectedListingId(null);
  };

  const summary = reportQuery.data?.summary;
  const listingItems = reportQuery.data?.items ?? [];

  return (
    <ModuleLayout
      moduleCode="HQA"
      user={user}
      title={`${title} Daily Report`}
      subtitle="Báo cáo listing theo ngày"
    >
      <PageHeader
        title={`${title} Daily Report`}
        subtitle="Ngày báo cáo lấy theo lần cập nhật gần nhất; chưa cập nhật thì dùng lần ghi nhận đầu tiên"
      />

      <MarketplaceTabs
        marketplace={marketplace}
      />

      <section className="report-summary-grid">
        <article className="report-summary-card">
          <span>Total listings on selected date</span>
          <strong>
            {summary?.total_listings_on_selected_date ?? 0}
          </strong>
        </article>

        <article className="report-summary-card">
          <span>New listings qualified</span>
          <strong>
            {summary?.new_listings_qualified ?? 0}
          </strong>
        </article>

        <article className="report-summary-card">
          <span>Ended listings</span>
          <strong>
            {summary?.ended_listings ?? 0}
          </strong>
        </article>

        <article className="report-summary-card">
          <span>Out of stock</span>
          <strong>
            {summary?.out_of_stock ?? 0}
          </strong>
        </article>
      </section>

      <section className="surface daily-report-filter">
        <div className="daily-report-filter-grid">
          <label className="field-stack">
            <span className="field-label">
              Report date
            </span>

            <input
              type="date"
              value={form.date ?? ''}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  date: event.target.value || undefined,
                }))
              }
            />
          </label>

          <FacetMultiSelect
            label="Status"
            value={form.status}
            options={reportQuery.data?.status_options ?? []}
            searchable={false}
            placeholder="All statuses"
            onApply={(values) =>
              setForm((current) => ({
                ...current,
                status: values,
              }))
            }
          />

          <label className="field-stack">
            <span className="field-label">
              Sort
            </span>

            <select
              value={form.sort}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  sort: event.target.value as DailyReportParams['sort'],
                }))
              }
            >
              <option value="last_updated_desc">
                Last updated
              </option>
              <option value="price_desc">
                Price high to low
              </option>
              <option value="price_asc">
                Price low to high
              </option>
              <option value="title_asc">
                Listing title A-Z
              </option>
            </select>
          </label>

          <label className="field-stack">
            <span className="field-label">
              Report table
            </span>

            <select
              value={form.table}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  table: event.target.value as DailyReportParams['table'],
                }))
              }
            >
              {tableOptions.map((option) => (
                <option
                  key={option.key}
                  value={option.key}
                >
                  {option.label} ({option.count})
                </option>
              ))}
            </select>
          </label>

          <label className="field-stack">
            <span className="field-label">
              Page size
            </span>

            <select
              value={form.page_size}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  page_size: Number(event.target.value),
                }))
              }
            >
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
        </div>

        <div className="filter-actions">
          <button
            type="button"
            className="action-button"
            onClick={applyFilters}
          >
            Apply filter
          </button>

          <button
            type="button"
            className="action-button secondary"
            onClick={resetFilters}
          >
            Reset filter
          </button>
        </div>
      </section>

      {reportQuery.isLoading ? (
        <LoadingScreen
          label="Đang tải daily report..."
        />
      ) : null}

      {reportQuery.isError ? (
        <ErrorState
          title="Không thể tải daily report"
          message="Vui lòng kiểm tra API hoặc quyền truy cập."
          action={
            <button
              type="button"
              className="action-button"
              onClick={() => {
                void reportQuery.refetch();
              }}
            >
              Thử lại
            </button>
          }
        />
      ) : null}

      {!reportQuery.isLoading
        && !reportQuery.isError
        && listingItems.length === 0 ? (
        <EmptyState
          title="Không có dữ liệu"
          message="Không tìm thấy listing phù hợp với ngày và bộ lọc hiện tại."
        />
      ) : null}

      {!reportQuery.isLoading
        && !reportQuery.isError
        && listingItems.length > 0 ? (
        <section
          style={{
            padding: '1rem',
            borderRadius: '18px',
            overflow: 'auto',
            background: '#fff',
            boxShadow: '0 24px 60px rgba(15, 23, 42, 0.12)',
          }}
        >
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              minWidth: '900px',
            }}
          >
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
                <tr
                  key={item.id}
                  style={{
                    borderTop: '1px solid var(--border)',
                  }}
                >
                  <td style={{ padding: '0.65rem' }}>
                    <a
                      href={item.listing_url}
                      target="_blank"
                      rel="noreferrer"
                      className="report-listing-link"
                    >
                      {item.listing_title}
                    </a>
                  </td>
                  <td style={{ padding: '0.65rem' }}>
                    {item.external_listing_id}
                  </td>
                  <td style={{ padding: '0.65rem' }}>
                    {item.seller_name ?? item.shop_name ?? 'N/A'}
                  </td>
                  <td style={{ padding: '0.65rem' }}>
                    {formatPrice(item.current_price, item.currency)}
                  </td>
                  <td style={{ padding: '0.65rem' }}>
                    {item.listing_status}
                  </td>
                  <td style={{ padding: '0.65rem' }}>
                    {formatDateTime(item.report_at)}
                  </td>
                  <td style={{ padding: '0.65rem' }}>
                    <button
                      className="action-button"
                      type="button"
                      style={{
                        minHeight: '2.2rem',
                        padding: '0.45rem 0.8rem',
                      }}
                      onClick={() => setSelectedListingId(item.id)}
                    >
                      Xem chi tiết
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div
            style={{
              display: 'flex',
              gap: '0.5rem',
              marginTop: '1rem',
              marginBottom: '1rem',
              flexWrap: 'wrap',
            }}
          >
            {pageItems.map((page) => (
              <button
                key={page}
                type="button"
                className="action-button"
                style={{
                  minHeight: '2.4rem',
                  padding: '0.35rem 0.65rem',
                  background:
                    page === filters.page
                      ? 'linear-gradient(135deg, var(--hqa), #6366f1)'
                      : 'rgba(79, 70, 229, 0.16)',
                  color:
                    page === filters.page
                      ? 'white'
                      : 'var(--text)',
                  boxShadow: 'none',
                }}
                onClick={() => {
                  setFilters((current) => ({
                    ...current,
                    page,
                  }));
                }}
              >
                {page}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {selectedListingId ? (
        <ListingDetailModal
          open={Boolean(selectedListingId)}
          detail={listingDetailQuery.data}
          history={listingHistoryQuery.data}
          detailLoading={listingDetailQuery.isLoading}
          historyLoading={listingHistoryQuery.isLoading}
          detailError={listingDetailQuery.isError}
          historyError={listingHistoryQuery.isError}
          onClose={() => setSelectedListingId(null)}
          onRetryDetail={() => {
            void listingDetailQuery.refetch();
          }}
          onRetryHistory={() => {
            void listingHistoryQuery.refetch();
          }}
        />
      ) : null}
    </ModuleLayout>
  );
}
