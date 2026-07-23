import axios from 'axios';

import { getAccessToken } from '@/auth/sessionStore';

const baseUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_AUTH_API_URL || '';

export function getApiBaseUrl() {
  return baseUrl;
}

export const rawApi = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

rawApi.interceptors.request.use((config) => {
  const accessToken = getAccessToken();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});
