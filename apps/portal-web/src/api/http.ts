import axios, {
  AxiosError,
  type InternalAxiosRequestConfig,
} from 'axios';

import { rawApi } from '@/api/rawClient';

import { refreshSession } from '@/auth/sessionActions';

import {
  getAccessToken,
  getIdleExpiresAt,
  triggerSessionExpired,
} from '@/auth/sessionStore';

interface RetryableRequestConfig
  extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

export const apiClient = axios.create({
  baseURL: rawApi.defaults.baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (
    config: InternalAxiosRequestConfig,
  ) => {
    const accessToken =
      getAccessToken();

    if (accessToken) {
      config.headers.Authorization =
        `Bearer ${accessToken}`;
    }

    return config;
  },
);

apiClient.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const status =
      error.response?.status;

    const config =
      error.config as
      | RetryableRequestConfig
      | undefined;

    const requestUrl = String(
      config?.url ?? '',
    );

    const isAuthRequest =
      requestUrl.includes('/api/auth/login') ||
      requestUrl.includes('/api/auth/refresh') ||
      requestUrl.includes('/api/auth/logout');

    if (
      status !== 401 ||
      !config ||
      isAuthRequest
    ) {
      return Promise.reject(error);
    }

    const idleExpiresAt =
      getIdleExpiresAt();

    // Không refresh khi đã quá 15 phút không thao tác.
    if (
      !idleExpiresAt ||
      idleExpiresAt <= Date.now()
    ) {
      triggerSessionExpired();
      return Promise.reject(error);
    }

    // Request đã retry một lần mà vẫn 401.
    if (config._retry) {
      triggerSessionExpired();
      return Promise.reject(error);
    }

    config._retry = true;

    try {
      const newAccessToken =
        await refreshSession();

      if (!newAccessToken) {
        throw new Error(
          'Không thể refresh access token.',
        );
      }

      config.headers.Authorization =
        `Bearer ${newAccessToken}`;

      return apiClient.request(config);
    } catch {
      triggerSessionExpired();
      return Promise.reject(error);
    }
  },
);