export type Marketplace = 'ebay' | 'reverb' | 'etsy';

export interface PageResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface MarketplaceDashboard {
  active_listings: number;
  new_today: number;
  last_sync_at: string | null;
  sync_status: string | null;
}

export interface HqaDashboardResponse {
  ebay: MarketplaceDashboard;
  reverb: MarketplaceDashboard;
  etsy: MarketplaceDashboard;
}

export interface ListingListItem {
  id: string;
  external_listing_id: string;
  listing_title: string;
  listing_url: string;
  seller_name: string | null;
  shop_name: string | null;
  shop_id: string | null;
  published_at: string | null;
  listing_location: string | null;
  country_code: string | null;
  category_id: string | null;
  category_name: string | null;
  condition_id: string | null;
  condition_name: string | null;
  image_url: string | null;
  current_price: string | null;
  shipping_price: string | null;
  total_price: string | null;
  currency: string | null;
  quantity: number | null;
  listing_views: number | null;
  listing_status: string;
  status_reason: string | null;
  first_seen_at: string;
  last_seen_at: string;
  state_hash: string | null;
}

export interface ListingDetailResponse extends ListingListItem {
  raw_payload: Record<string, unknown> | null;
  buying_options: Record<string, unknown> | null;
  etsy_data: Record<string, unknown> | null;
}

export interface ListingSnapshotItem {
  id: string;
  listing_id: string;
  observed_at: string;
  price: string | null;
  shipping_price: string | null;
  total_price: string | null;
  currency: string | null;
  quantity: number | null;
  listing_views: number | null;
  listing_status: string | null;
  status_reason: string | null;
  state_hash: string;
  raw_payload: Record<string, unknown> | null;
  created_at: string;
}

export interface SyncJobResponse {
  id: string;
  marketplace: Marketplace;
  trigger_type: string;
  status: 'queued' | 'running' | 'success' | 'partial_success' | 'failed' | string;
  scheduled_for: string | null;
  started_at: string | null;
  completed_at: string | null;
  total_source_rows: number;
  inserted_rows: number;
  updated_rows: number;
  unchanged_rows: number;
  skipped_rows: number;
  error_rows: number;
  requested_by_user_id: string | null;
  error_summary: string | null;
  metadata_: Record<string, unknown> | null;
  created_at: string;
}

export interface SyncTriggerResponse {
  job_id: string;
  status: 'queued';
  marketplace: Marketplace;
}

export interface BatchSyncTriggerResponse {
  items: SyncTriggerResponse[];
}

export type ListingSortBy =
  | 'last_seen_at'
  | 'published_at'
  | 'status'
  | 'category'
  | 'condition'
  | 'seller'
  | 'price';

export type ListingSortOrder = 'asc' | 'desc';

export interface ListingListParams {
  page: number;
  page_size: number;

  q?: string;

  status?: string[];
  category?: string[];
  condition?: string[];
  seller?: string[];
  currency?: string[];

  min_price?: string;
  max_price?: string;

  date_from?: string;
  date_to?: string;

  sort_by?: ListingSortBy;
  sort_order?: ListingSortOrder;
}

export interface ListingFacetOption {
  value: string;
  label: string;
  count: number;
}

export interface ListingPriceRange {
  min: string | null;
  max: string | null;
}

export interface ListingFilterOptions {
  status: ListingFacetOption[];
  category: ListingFacetOption[];
  condition: ListingFacetOption[];
  seller: ListingFacetOption[];
  currency: ListingFacetOption[];
  price_range: ListingPriceRange;
}

export type ListingExportFormat =
  | 'xlsx'
  | 'pdf'
  | 'google_sheets';

export type ListingExportFilters = Omit<
  ListingListParams,
  'page' | 'page_size'
>;

export interface ListingExportRequest {
  format: ListingExportFormat;
  fields: string[];
  filters: ListingExportFilters;
}

export interface GoogleSheetsExportResponse {
  spreadsheet_id: string;
  spreadsheet_url: string;
  exported_rows: number;
}

export type ListingExportResult =
  | {
    kind: 'file';
    blob: Blob;
    filename: string;
  }
  | {
    kind: 'google_sheets';
    data: GoogleSheetsExportResponse;
  };