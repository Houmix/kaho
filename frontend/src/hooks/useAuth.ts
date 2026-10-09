import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'STUDENT' | 'INSTRUCTOR' | 'SUPERVISOR' | 'ADMIN' | 'OWNER';
  also_instructor?: boolean;
  teaches?: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  // false until the persisted state has been read back from localStorage
  hasHydrated: boolean;

  setToken: (token: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      hasHydrated: false,

      setToken: (token, refreshToken) => set({ token, refreshToken, isAuthenticated: true }),
      setUser: (user) => set({ user, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, refreshToken: null, isAuthenticated: false }),
      setHasHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: 'auth-storage',
      partialize: (s) => ({ user: s.user, token: s.token, refreshToken: s.refreshToken, isAuthenticated: s.isAuthenticated }),
      onRehydrateStorage: () => (state) => state?.setHasHydrated(true),
    }
  )
);

export function getAuthStore() {
  return useAuthStore.getState();
}

export function useAuth() {
  return useAuthStore();
}
