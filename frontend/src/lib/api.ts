import axios, { AxiosInstance, AxiosError } from 'axios';
import { getAuthStore } from '@/hooks/useAuth';
import { addToSyncQueue, getSyncQueue, clearSyncQueue } from './db';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Add JWT token
api.interceptors.request.use(
  (config) => {
    const { token } = getAuthStore();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle token refresh and offline
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    // Handle 401 - Token expired
    if (error.response?.status === 401 && originalRequest && !(originalRequest as any)._anonRetry) {
      const { refreshToken, setToken } = getAuthStore();
      const hadAuth = !!originalRequest.headers?.Authorization;

      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          setToken(access, refreshToken);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access}`;
          }

          return api(originalRequest);
        } catch (refreshError) {
          getAuthStore().logout();
        }
      }
      // Jeton invalide ou expiré sans rafraîchissement possible : les pages publiques
      // (démo, cours en accès libre) doivent continuer à fonctionner en anonyme.
      if (hadAuth) {
        (originalRequest as any)._anonRetry = true;
        if (originalRequest.headers) delete originalRequest.headers.Authorization;
        return axios(originalRequest);
      }
    }

    // Handle offline - Queue request for later
    if (!navigator.onLine && originalRequest && originalRequest.method !== 'GET') {
      await addToSyncQueue({
        method: originalRequest.method || 'GET',
        url: originalRequest.url || '',
        data: originalRequest.data,
        timestamp: Date.now(),
      });
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

// Sync offline queue when connection is restored
if (typeof window !== 'undefined') {
  window.addEventListener('online', async () => {
    const queue = await getSyncQueue();

    for (const request of queue) {
      try {
        await api({
          method: request.method as any,
          url: request.url,
          data: request.data,
        });
      } catch (error) {
        console.error('Error syncing request:', error);
      }
    }

    if (queue.length > 0) {
      await clearSyncQueue();
    }
  });
}

export default api;
