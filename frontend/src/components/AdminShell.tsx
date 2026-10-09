import { ReactNode, useEffect, useRef, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { SearchResults } from '@/lib/admin';
import Logo from './Logo';

const NAV: { href: string; label: string; icon: string; soon?: boolean; external?: boolean; owner?: boolean }[] = [
  { href: '/admin', label: 'Tableau de bord', icon: '▦' },
  { href: '/admin/students', label: 'Apprenants', icon: '◉' },
  { href: '/admin/instructors', label: 'Formateurs', icon: '◆' },
  { href: '/admin/calendar', label: 'Planning', icon: '▤' },
  { href: '/admin/reviews', label: 'Avis', icon: '★' },
  { href: '/instructor/performance', label: 'Performance', icon: '◔' },
  { href: '/admin/activity', label: 'Activité', icon: '≡' },
  { href: '/admin/sales', label: 'Ventes & factures', icon: '◫', owner: true },
  { href: '/admin/lms', label: 'Contenus LMS', icon: '▣' },
  { href: '/admin/offers', label: 'Offres & tarifs', icon: '◈', owner: true },
  { href: '/admin/team', label: 'Équipe admin', icon: '⚑', owner: true },
];
export const ROLE_LABELS: Record<string, string> = { OWNER: 'Gérant (super admin)', ADMIN: "Gestionnaire d'exploitation", SUPERVISOR: 'Superviseur', INSTRUCTOR: 'Moniteur', STUDENT: 'Élève' };

function GlobalSearch() {
  const [q, setQ] = useState('');
  const [res, setRes] = useState<SearchResults | null>(null);
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (q.trim().length < 2) { setRes(null); return; }
    const t = setTimeout(() => api.get('/admin/search/', { params: { q } }).then((r) => { setRes(r.data); setOpen(true); }), 250);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const go = (href: string) => { setOpen(false); setQ(''); router.push(href); };
  const groups: { title: string; items: { href: string; label: string; sub?: string }[] }[] = res ? [
    { title: 'Apprenants', items: res.students.map((s) => ({ href: s.href, label: s.name, sub: `${s.email} · ${s.remaining_hours.toFixed(1)} h` })) },
    { title: 'Formateurs', items: res.instructors.map((i) => ({ href: i.href, label: i.name, sub: i.email })) },
    { title: 'Achats', items: res.packages.map((p) => ({ href: p.href, label: p.label, sub: p.status })) },
    { title: 'Créneaux', items: res.slots.map((s) => ({ href: s.href, label: s.label, sub: s.status })) },
  ].filter((g) => g.items.length) : [];

  return (
    <div ref={box} className="relative flex-1 max-w-xl">
      <input value={q} onChange={(e) => setQ(e.target.value)} onFocus={() => res && setOpen(true)}
        placeholder="Rechercher un élève, un moniteur, un achat (#12), une date (2026-10-12)…"
        className="input-field !py-2 !rounded-full" aria-label="Recherche globale" />
      {open && res && (
        <div className="absolute z-20 mt-2 w-full card p-2 max-h-96 overflow-auto">
          {groups.length === 0 ? <p className="p-3 text-sm text-brown-800/60">Aucun résultat.</p> : groups.map((g) => (
            <div key={g.title} className="mb-2">
              <p className="px-3 pt-2 pb-1 text-xs uppercase tracking-wide text-caramel font-medium">{g.title}</p>
              {g.items.map((it, i) => (
                <button key={i} onClick={() => go(it.href)} className="w-full text-left px-3 py-2 rounded-lg hover:bg-cream-100">
                  <div className="font-medium text-sm">{it.label}</div>
                  {it.sub && <div className="text-xs text-brown-800/60">{it.sub}</div>}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AdminShell({ title, children, wide = false }: { title: string; children: ReactNode; wide?: boolean }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [drawer, setDrawer] = useState(false);
  const isActive = (href: string) => router.pathname === href || (href !== '/admin' && router.pathname.startsWith(href)) || (href === '/admin/calendar' && router.pathname === '/instructor/planning');

  const isOwner = user?.role === 'OWNER';
  const Nav = () => (
    <nav className="flex flex-col gap-0.5">
      {NAV.filter((n) => !n.owner || isOwner).map((n) => n.soon ? (
        <span key={n.href} className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-brown-800/40 cursor-not-allowed" title="Bientôt disponible">
          <span className="w-5 text-center">{n.icon}</span>{n.label}<span className="ml-auto text-[10px] uppercase tracking-wide">bientôt</span>
        </span>
      ) : (
        <Link key={n.href} href={n.href} onClick={() => setDrawer(false)}
          className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium ${isActive(n.href) ? 'bg-brown-700 text-cream-50' : 'text-brown-800 hover:bg-cream-200'}`}>
          <span className="w-5 text-center">{n.icon}</span>{n.label}
        </Link>
      ))}
    </nav>
  );

  return (
    <>
      <Head><title>{`${title} — Kaho`}</title></Head>
      <div className="min-h-screen md:grid md:grid-cols-[240px_1fr]">
        <aside className="hidden md:flex flex-col bg-white border-r border-cream-200 p-4 sticky top-0 h-screen">
          <div className="mb-6 px-1"><Logo /></div>
          <Nav />
          <div className="mt-auto pt-4 border-t border-cream-200 text-sm">
            <div className="font-medium truncate">{user?.first_name} {user?.last_name}</div>
            <div className="text-brown-800/60 text-xs mb-2">{ROLE_LABELS[user?.role ?? ''] ?? ''}</div>
            <button onClick={() => { logout(); router.push('/login'); }} className="text-brown-700 hover:underline">Déconnexion</button>
          </div>
        </aside>

        <div className="min-w-0">
          <header className="bg-white border-b border-cream-200 sticky top-0 z-10">
            <div className="flex items-center gap-3 px-4 py-3">
              <button onClick={() => setDrawer(true)} className="md:hidden btn-secondary !px-3 !py-2" aria-label="Menu">☰</button>
              <div className="md:hidden"><Logo className="h-7" /></div>
              <GlobalSearch />
            </div>
          </header>
          <main className={`px-4 py-6 ${wide ? '' : 'max-w-6xl'}`}>{children}</main>
        </div>
      </div>

      {drawer && (
        <div className="md:hidden fixed inset-0 z-30 bg-brown-900/40" onClick={() => setDrawer(false)}>
          <aside className="absolute left-0 top-0 h-full w-72 bg-white p-4 overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6"><Logo /><button onClick={() => setDrawer(false)} aria-label="Fermer">✕</button></div>
            <Nav />
            <button onClick={() => { logout(); router.push('/login'); }} className="mt-6 text-sm text-brown-700 hover:underline">Déconnexion</button>
          </aside>
        </div>
      )}
    </>
  );
}
