import axios, {
  AxiosError,
  type InternalAxiosRequestConfig,
} from 'axios';

import {
  getAccessToken,
  triggerSessionExpired,
} from '@/auth/sessionStore';

import { rawApi } from '@/api/rawClient';

export const apiClient = axios.create({
  baseURL: rawApi.defaults.baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const accessToken = getAccessToken();

    if (accessToken) {
      config.headers.Authorization =
        `Bearer ${accessToken}`;
    }

    return config;
  },
);

apiClient.interceptors.response.use(
  (response) => response,

  (error: AxiosError) => {
    const status = error.response?.status;
    const requestUrl = String(error.config?.url ?? '');

    if (
      status === 401 &&
      !requestUrl.includes('/api/auth/login')
    ) {
      triggerSessionExpired();
    }

    return Promise.reject(error);
  },
);
