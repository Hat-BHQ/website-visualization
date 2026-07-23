import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { refreshSession } from '@/auth/sessionActions';
import { getAccessToken, getRefreshToken, triggerSessionExpired } from '@/auth/sessionStore';
import { rawApi } from '@/api/rawClient';

export const apiClient = axios.create({
  baseURL: rawApi.defaults.baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const accessToken = getAccessToken();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean } | undefined;
    const status = error.response?.status;

    if (status === 401 && originalRequest && !originalRequest._retry && !String(originalRequest.url ?? '').includes('/api/auth/refresh')) {
      originalRequest._retry = true;
      try {
        const tokens = getRefreshToken();
        if (!tokens) {
          throw new Error('Missing refresh token');
        }
        const refreshed = await refreshSession();
        originalRequest.headers.Authorization = `Bearer ${refreshed.tokens.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        triggerSessionExpired();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);
