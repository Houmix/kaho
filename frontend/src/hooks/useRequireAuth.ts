import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuthStore, User } from './useAuth';

type Role = User['role'];
export const STAFF_ROLES: Role[] = ['INSTRUCTOR', 'SUPERVISOR', 'ADMIN', 'OWNER'];
export const BACKOFFICE: Role[] = ['SUPERVISOR', 'ADMIN', 'OWNER'];

// Returns true once the session is restored AND the user has one of the allowed roles. Redirects to /login otherwise.
export function useRequireAuth(roles?: Role | Role[]): boolean {
  const { hasHydrated, isAuthenticated, user } = useAuthStore();
  const router = useRouter();
  const allowedRoles = roles === undefined ? null : Array.isArray(roles) ? roles : [roles];
  const allowed = hasHydrated && isAuthenticated && (!allowedRoles || (!!user && allowedRoles.includes(user.role)));

  useEffect(() => {
    if (hasHydrated && !allowed) router.replace('/login');
  }, [hasHydrated, allowed, router]);

  return allowed;
}

export function homeFor(role?: Role): string {
  if (role === 'STUDENT') return '/student/dashboard';
  if (role === 'INSTRUCTOR') return '/instructor/dashboard';
  return '/admin';
}
