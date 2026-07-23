import { AxiosError, isAxiosError } from 'axios';

export function getHttpStatus(error: unknown): number | null {
  if (isAxiosError(error)) {
    return error.response?.status ?? null;
  }
  return null;
}

export function isForbiddenError(error: unknown): boolean {
  return getHttpStatus(error) === 403;
}

export function getConflictMessage(error: unknown): string | null {
  if (!isAxiosError(error)) {
    return null;
  }

  if (error.response?.status !== 409) {
    return null;
  }

  const detail = error.response.data as { detail?: unknown } | undefined;
  if (!detail || typeof detail.detail !== 'object' || detail.detail === null) {
    return 'Marketplace đang đồng bộ. Vui lòng chờ job hiện tại hoàn tất.';
  }

  const payload = detail.detail as { message?: string; active_job_id?: string | null };
  if (payload.message && payload.active_job_id) {
    return `${payload.message} (job: ${payload.active_job_id})`;
  }
  if (payload.message) {
    return payload.message;
  }
  return 'Marketplace đang đồng bộ. Vui lòng chờ job hiện tại hoàn tất.';
}
