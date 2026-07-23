import { rawApi } from '@/api/rawClient';
import type { CurrentUser, TokenPairResponse } from '@/types/auth';

export async function loginApi(email: string, password: string) {
  const response = await rawApi.post<TokenPairResponse>('/api/auth/login', { email, password });
  return response.data;
}

export async function refreshApi(refreshToken: string | null) {
  const response = await rawApi.post<TokenPairResponse>('/api/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
}

export async function logoutApi(refreshToken: string | null) {
  await rawApi.post('/api/auth/logout', {
    refresh_token: refreshToken,
  });
}

export async function meApi() {
  const response = await rawApi.get<CurrentUser>('/api/auth/me');
  return response.data;
}
