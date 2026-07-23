import { apiClient } from '@/api/http';
import type {
  BatchSyncTriggerResponse,
  HqaDashboardResponse,
  ListingDetailResponse,
  ListingListItem,
  ListingListParams,
  ListingSnapshotItem,
  Marketplace,
  PageResponse,
  SyncJobResponse,
  SyncTriggerResponse,
} from '@/types/hqa';

const hqaBaseUrl = import.meta.env.VITE_HQA_API_URL || apiClient.defaults.baseURL || '';

function normalizeParams(params: ListingListParams) {
  const clean: Record<string, string | number> = {
    page: params.page,
    page_size: params.page_size,
  };

  if (params.q) clean.q = params.q;
  if (params.status) clean.status = params.status;
  if (params.category) clean.category = params.category;
  if (params.condition) clean.condition = params.condition;
  if (params.seller) clean.seller = params.seller;
  if (params.min_price) clean.min_price = params.min_price;
  if (params.max_price) clean.max_price = params.max_price;
  if (params.date_from) clean.date_from = params.date_from;
  if (params.date_to) clean.date_to = params.date_to;
  if (params.sort_by) clean.sort_by = params.sort_by;
  if (params.sort_order) clean.sort_order = params.sort_order;

  return clean;
}

export async function getHqaDashboard() {
  const response = await apiClient.get<HqaDashboardResponse>('/api/hqa/dashboard', {
    baseURL: hqaBaseUrl,
  });
  return response.data;
}

export async function getMarketplaceListings(marketplace: Marketplace, params: ListingListParams) {
  const response = await apiClient.get<PageResponse<ListingListItem>>(`/api/hqa/${marketplace}/listings`, {
    baseURL: hqaBaseUrl,
    params: normalizeParams(params),
  });
  return response.data;
}

export async function getMarketplaceListingDetail(marketplace: Marketplace, id: string) {
  const response = await apiClient.get<ListingDetailResponse>(`/api/hqa/${marketplace}/listings/${id}`, {
    baseURL: hqaBaseUrl,
  });
  return response.data;
}

export async function getMarketplaceListingHistory(marketplace: Marketplace, id: string) {
  const response = await apiClient.get<ListingSnapshotItem[]>(`/api/hqa/${marketplace}/listings/${id}/history`, {
    baseURL: hqaBaseUrl,
  });
  return response.data;
}

export async function getSyncJobs(marketplace?: Marketplace) {
  const response = await apiClient.get<SyncJobResponse[]>('/api/hqa/sync-jobs', {
    baseURL: hqaBaseUrl,
    params: marketplace ? { marketplace } : undefined,
  });
  return response.data;
}

export async function getSyncJob(jobId: string) {
  const response = await apiClient.get<SyncJobResponse>(`/api/hqa/sync-jobs/${jobId}`, {
    baseURL: hqaBaseUrl,
  });
  return response.data;
}

export async function triggerSyncAll() {
  const response = await apiClient.post<BatchSyncTriggerResponse>('/api/hqa/sync', undefined, {
    baseURL: hqaBaseUrl,
  });
  return response.data;
}

export async function triggerSyncMarketplace(marketplace: Marketplace) {
  const response = await apiClient.post<SyncTriggerResponse>(`/api/hqa/sync/${marketplace}`, undefined, {
    baseURL: hqaBaseUrl,
  });
  return response.data;
}
