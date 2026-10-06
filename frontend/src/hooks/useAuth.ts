import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'INSTRUCTOR' | 'STUDENT';
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  setToken: (token: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  setError: (error: string | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isLoading: false,
      error: null,
      isAuthenticated: false,

      setToken: (token: string, refreshToken: string) =>
        set({
          token,
          refreshToken,
          isAuthenticated: true,
        }),

      setUser: (user: User) =>
        set({
          user,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        }),

      setError: (error: string | null) =>
        set({ error }),
    }),
    {
      name: 'auth-storage',
    }
  )
);

export function getAuthStore() {
  return useAuthStore.getState();
}

export function useAuth() {
  return useAuthStore();
}
