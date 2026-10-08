import { ReactNode } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import AdminShell from './AdminShell';
import Logo from './Logo';

const STUDENT_NAV = [
  { href: '/student/dashboard', label: 'Mon espace' },
  { href: '/student/reservation', label: 'Réserver' },
  { href: '/code', label: 'Code' },
  { href: '/student/notebook', label: 'Livret' },
  { href: '/student/documents', label: 'Documents' },
  { href: '/student/purchases', label: 'Offres' },
];
const INSTRUCTOR_NAV = [
  { href: '/instructor/dashboard', label: 'Tableau de bord' },
  { href: '/instructor/planning', label: 'Planning' },
  { href: '/instructor/availability', label: 'Disponibilités' },
];
export default function AppShell({ title, children }: { title: string; children: ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  if (user?.role === 'ADMIN' || user?.role === 'SUPERVISOR' || user?.role === 'OWNER') {
    return <AdminShell title={title} wide>{children}</AdminShell>;
  }
  const nav = user?.role === 'STUDENT' ? STUDENT_NAV : INSTRUCTOR_NAV;
  const linkCls = (href: string) =>
    `px-3 py-2 rounded-full text-sm font-medium ${router.pathname === href || (href === '/code' && router.pathname.startsWith('/code')) ? 'bg-brown-700 text-cream-50' : 'text-brown-800 hover:bg-cream-200'}`;

  return (
    <>
      <Head><title>{`${title} — Kaho`}</title></Head>
      <header className="bg-white border-b border-cream-200">
        <div className="container flex items-center justify-between py-3 gap-3">
          <Logo />
          <nav className="hidden sm:flex items-center gap-1">
            {nav.map((n) => <Link key={n.href} href={n.href} className={linkCls(n.href)}>{n.label}</Link>)}
          </nav>
          <button onClick={() => { logout(); router.push('/login'); }} className="btn-secondary !px-4 !py-2 text-sm">Déconnexion</button>
        </div>
      </header>

      <main className="container py-6 pb-24 sm:pb-10">{children}</main>

      <nav className="sm:hidden fixed bottom-0 inset-x-0 bg-white border-t border-cream-200 flex">
        {nav.map((n) => (
          <Link key={n.href} href={n.href}
            className={`flex-1 text-center py-3 text-sm font-medium ${router.pathname === n.href ? 'text-brown-700 border-t-2 border-brown-700 -mt-px' : 'text-brown-800/60'}`}>
            {n.label}
          </Link>
        ))}
      </nav>
    </>
  );
}
