import { apiClient } from '@/api/http';

import type {
  BatchSyncTriggerResponse,
  HqaDashboardResponse,
  ListingDetailResponse,
  ListingFilterOptions,
  ListingListItem,
  ListingListParams,
  ListingSnapshotItem,
  Marketplace,
  PageResponse,
  SyncJobResponse,
  SyncTriggerResponse,
  GoogleSheetsExportResponse,
  ListingExportRequest,
  ListingExportResult,
} from '@/types/hqa';

/**
 * Có thể cấu hình riêng URL cho HQA Service bằng biến:
 *
 * VITE_HQA_API_URL=http://localhost:8002
 *
 * Nếu không có, hệ thống sẽ sử dụng baseURL đã cấu hình
 * trong apiClient.
 */
const hqaBaseUrl =
  import.meta.env.VITE_HQA_API_URL ||
  apiClient.defaults.baseURL ||
  '';

interface BuildSearchParamsOptions {
  includePagination?: boolean;
  includeSort?: boolean;
}

/**
 * Thêm nhiều giá trị cùng một query key.
 *
 * Ví dụ:
 *
 * status=active&status=ended
 *
 * FastAPI sẽ nhận được:
 *
 * status: list[str] | None
 */
function appendMany(
  searchParams: URLSearchParams,
  key: string,
  values?: string[],
) {
  if (!values || values.length === 0) {
    return;
  }

  values.forEach((value) => {
    const normalizedValue = value.trim();

    if (normalizedValue) {
      searchParams.append(key, normalizedValue);
    }
  });
}

function getDownloadFilename(
  contentDisposition?: string,
) {
  if (!contentDisposition) {
    return null;
  }

  const utf8Match =
    contentDisposition.match(
      /filename\*=UTF-8''([^;]+)/i,
    );

  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const normalMatch =
    contentDisposition.match(
      /filename="?([^"]+)"?/i,
    );

  return normalMatch?.[1] ?? null;
}

/**
 * Export listing theo bộ filter hiện đang được áp dụng.
 */
export async function exportMarketplaceListings(
  marketplace: Marketplace,
  payload: ListingExportRequest,
): Promise<ListingExportResult> {
  const endpoint =
    `/api/hqa/${marketplace}/listings/export`;

  if (payload.format === 'google_sheets') {
    const response =
      await apiClient.post<
        GoogleSheetsExportResponse
      >(
        endpoint,
        payload,
        {
          baseURL: hqaBaseUrl,
        },
      );

    return {
      kind: 'google_sheets',
      data: response.data,
    };
  }

  const response =
    await apiClient.post<Blob>(
      endpoint,
      payload,
      {
        baseURL: hqaBaseUrl,
        responseType: 'blob',
      },
    );

  const defaultExtension =
    payload.format === 'pdf'
      ? 'pdf'
      : 'xlsx';

  const filename =
    getDownloadFilename(
      response.headers[
      'content-disposition'
      ],
    ) ??
    `hqa_${marketplace}_export.${defaultExtension}`;

  return {
    kind: 'file',
    blob: response.data,
    filename,
  };
}

/**
 * Chuyển ListingListParams thành query string.
 *
 * Danh sách listing:
 * - Có page và page_size.
 * - Có sort_by và sort_order.
 *
 * Filter options:
 * - Không cần page và page_size.
 * - Không cần sort.
 */
function buildListingSearchParams(
  params: ListingListParams,
  options: BuildSearchParamsOptions = {},
) {
  const {
    includePagination = true,
    includeSort = true,
  } = options;

  const searchParams = new URLSearchParams();

  if (includePagination) {
    searchParams.set('page', String(params.page));
    searchParams.set(
      'page_size',
      String(params.page_size),
    );
  }

  const keyword = params.q?.trim();

  if (keyword) {
    searchParams.set('q', keyword);
  }

  appendMany(
    searchParams,
    'status',
    params.status,
  );

  appendMany(
    searchParams,
    'category',
    params.category,
  );

  appendMany(
    searchParams,
    'condition',
    params.condition,
  );

  appendMany(
    searchParams,
    'seller',
    params.seller,
  );

  appendMany(
    searchParams,
    'currency',
    params.currency,
  );

  if (
    params.min_price !== undefined &&
    params.min_price !== ''
  ) {
    searchParams.set(
      'min_price',
      params.min_price,
    );
  }

  if (
    params.max_price !== undefined &&
    params.max_price !== ''
  ) {
    searchParams.set(
      'max_price',
      params.max_price,
    );
  }

  if (params.date_from) {
    searchParams.set(
      'date_from',
      params.date_from,
    );
  }

  if (params.date_to) {
    searchParams.set(
      'date_to',
      params.date_to,
    );
  }

  if (includeSort && params.sort_by) {
    searchParams.set(
      'sort_by',
      params.sort_by,
    );
  }

  if (includeSort && params.sort_order) {
    searchParams.set(
      'sort_order',
      params.sort_order,
    );
  }

  return searchParams.toString();
}

/**
 * Ghép endpoint với query string.
 */
function withQueryString(
  endpoint: string,
  queryString: string,
) {
  if (!queryString) {
    return endpoint;
  }

  return `${endpoint}?${queryString}`;
}

/**
 * Lấy dữ liệu dashboard tổng quan của module HQA.
 */
export async function getHqaDashboard() {
  const response =
    await apiClient.get<HqaDashboardResponse>(
      '/api/hqa/dashboard',
      {
        baseURL: hqaBaseUrl,
      },
    );

  return response.data;
}

/**
 * Lấy danh sách listing của một marketplace.
 *
 * Hỗ trợ:
 * - Phân trang.
 * - Tìm theo từ khóa.
 * - Multi-select status.
 * - Multi-select category.
 * - Multi-select condition.
 * - Multi-select seller.
 * - Multi-select currency.
 * - Khoảng giá.
 * - Khoảng ngày.
 * - Sort.
 */
export async function getMarketplaceListings(
  marketplace: Marketplace,
  params: ListingListParams,
) {
  const queryString =
    buildListingSearchParams(params, {
      includePagination: true,
      includeSort: true,
    });

  const endpoint = withQueryString(
    `/api/hqa/${marketplace}/listings`,
    queryString,
  );

  const response =
    await apiClient.get<
      PageResponse<ListingListItem>
    >(endpoint, {
      baseURL: hqaBaseUrl,
    });

  return response.data;
}

/**
 * Lấy các giá trị filter đang tồn tại trong database.
 *
 * Kết quả dự kiến gồm:
 * - status
 * - category
 * - condition
 * - seller
 * - currency
 * - price_range
 *
 * API này vẫn nhận các filter đang áp dụng để backend
 * có thể trả về faceted options phù hợp.
 */
export async function getMarketplaceFilterOptions(
  marketplace: Marketplace,
  params: ListingListParams,
) {
  const queryString =
    buildListingSearchParams(params, {
      includePagination: false,
      includeSort: false,
    });

  const endpoint = withQueryString(
    `/api/hqa/${marketplace}/listings/filter-options`,
    queryString,
  );

  const response =
    await apiClient.get<ListingFilterOptions>(
      endpoint,
      {
        baseURL: hqaBaseUrl,
      },
    );

  return response.data;
}

/**
 * Lấy chi tiết một listing.
 */
export async function getMarketplaceListingDetail(
  marketplace: Marketplace,
  id: string,
) {
  const response =
    await apiClient.get<ListingDetailResponse>(
      `/api/hqa/${marketplace}/listings/${id}`,
      {
        baseURL: hqaBaseUrl,
      },
    );

  return response.data;
}

/**
 * Lấy lịch sử snapshot của listing.
 */
export async function getMarketplaceListingHistory(
  marketplace: Marketplace,
  id: string,
) {
  const response =
    await apiClient.get<ListingSnapshotItem[]>(
      `/api/hqa/${marketplace}/listings/${id}/history`,
      {
        baseURL: hqaBaseUrl,
      },
    );

  return response.data;
}

/**
 * Lấy lịch sử các sync job.
 *
 * Nếu truyền marketplace thì chỉ lấy job của
 * marketplace đó.
 */
export async function getSyncJobs(
  marketplace?: Marketplace,
) {
  const response =
    await apiClient.get<SyncJobResponse[]>(
      '/api/hqa/sync-jobs',
      {
        baseURL: hqaBaseUrl,
        params: marketplace
          ? {
            marketplace,
          }
          : undefined,
      },
    );

  return response.data;
}

/**
 * Lấy chi tiết một sync job.
 */
export async function getSyncJob(
  jobId: string,
) {
  const response =
    await apiClient.get<SyncJobResponse>(
      `/api/hqa/sync-jobs/${jobId}`,
      {
        baseURL: hqaBaseUrl,
      },
    );

  return response.data;
}

/**
 * Chạy đồng bộ toàn bộ marketplace:
 * - eBay
 * - Reverb
 * - Etsy
 */
export async function triggerSyncAll() {
  const response =
    await apiClient.post<BatchSyncTriggerResponse>(
      '/api/hqa/sync',
      undefined,
      {
        baseURL: hqaBaseUrl,
      },
    );

  return response.data;
}

/**
 * Chạy đồng bộ một marketplace cụ thể.
 */
export async function triggerSyncMarketplace(
  marketplace: Marketplace,
) {
  const response =
    await apiClient.post<SyncTriggerResponse>(
      `/api/hqa/sync/${marketplace}`,
      undefined,
      {
        baseURL: hqaBaseUrl,
      },
    );

  return response.data;
}