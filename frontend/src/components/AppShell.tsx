import { ReactNode } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import AdminShell from './AdminShell';
import Logo from './Logo';

// `short` : libellé de la barre du bas sur téléphone (une seule ligne), `icon` : repère visuel
const STUDENT_NAV = [
  { href: '/student/dashboard', label: 'Mon espace', short: 'Accueil', icon: '⌂' },
  { href: '/student/reservation', label: 'Réserver', short: 'Réserver', icon: '▤' },
  { href: '/code', label: 'Code', short: 'Code', icon: '✎' },
  { href: '/student/notebook', label: 'Livret', short: 'Livret', icon: '☰' },
  { href: '/student/documents', label: 'Documents', short: 'Docs', icon: '▣' },
  { href: '/student/purchases', label: 'Offres', short: 'Offres', icon: '◈' },
];
const INSTRUCTOR_NAV = [
  { href: '/instructor/dashboard', label: 'Tableau de bord', short: 'Accueil', icon: '⌂' },
  { href: '/instructor/planning', label: 'Planning', short: 'Planning', icon: '▤' },
  { href: '/instructor/availability', label: 'Disponibilités', short: 'Dispos', icon: '◔' },
];
export default function AppShell({ title, children }: { title: string; children: ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  if (user?.role === 'ADMIN' || user?.role === 'SUPERVISOR' || user?.role === 'OWNER') {
    return <AdminShell title={title} wide>{children}</AdminShell>;
  }
  const nav = user?.role === 'STUDENT' ? STUDENT_NAV : INSTRUCTOR_NAV;
  const home = user?.role === 'STUDENT' ? '/student/dashboard' : '/instructor/dashboard';
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

      <main className="container py-6 pb-24 sm:pb-10">
        {router.pathname !== home && (
          <Link href={home} className="inline-flex items-center gap-1 text-sm text-brown-700 hover:underline mb-4 py-2">← Retour au tableau de bord</Link>
        )}
        {children}
      </main>

      <nav className="sm:hidden fixed bottom-0 inset-x-0 z-20 bg-white border-t border-cream-200 flex pb-[env(safe-area-inset-bottom)]" aria-label="Navigation principale">
        {nav.map((n) => {
          const active = router.pathname === n.href || (n.href === '/code' && router.pathname.startsWith('/code'));
          return (
            <Link key={n.href} href={n.href} aria-current={active ? 'page' : undefined}
              className={`flex-1 min-w-0 flex flex-col items-center justify-center gap-0.5 py-2 min-h-[56px] text-[11px] leading-tight font-medium whitespace-nowrap ${active ? 'text-brown-700 border-t-2 border-brown-700 -mt-px' : 'text-brown-800/60'}`}>
              <span aria-hidden className="text-base leading-none">{n.icon}</span>
              <span className="truncate max-w-full px-0.5">{n.short}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
