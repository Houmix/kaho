import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuthStore, User } from './useAuth';

// Returns true once the session is restored AND the user is allowed. Redirects to /login otherwise.
export function useRequireAuth(role?: User['role']): boolean {
  const { hasHydrated, isAuthenticated, user } = useAuthStore();
  const router = useRouter();
  const allowed = hasHydrated && isAuthenticated && (!role || user?.role === role);

  useEffect(() => {
    if (hasHydrated && !allowed) router.replace('/login');
  }, [hasHydrated, allowed, router]);

  return allowed;
}
