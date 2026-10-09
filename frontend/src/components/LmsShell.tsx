import { ReactNode, useEffect } from 'react';
import api from '@/lib/api';
import Head from 'next/head';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import AppShell from './AppShell';
import Logo from './Logo';

// Pages du LMS accessibles connecté (espace élève) ou non (chapitre de démonstration).
/** Comptabilise le temps passé sur le LMS (battement toutes les 60 s, élèves connectés uniquement). */
export function useStudyHeartbeat(active = true) {
  const { isAuthenticated, user } = useAuth();
  useEffect(() => {
    if (!active || !isAuthenticated || user?.role !== 'STUDENT') return;
    const tick = () => { if (document.visibilityState === 'visible') api.post('/lms/exam-attempts/heartbeat/', { seconds: 60 }).catch(() => {}); };
    const t = setInterval(tick, 60000);
    return () => clearInterval(t);
  }, [active, isAuthenticated, user]);
}

export default function LmsShell({ title, children }: { title: string; children: ReactNode }) {
  const { hasHydrated, isAuthenticated } = useAuth();
  useStudyHeartbeat();
  if (hasHydrated && isAuthenticated) return <AppShell title={title}>{children}</AppShell>;
  return (
    <>
      <Head><title>{`${title} — Kaho`}</title></Head>
      <header className="bg-white border-b border-cream-200">
        <div className="container flex items-center justify-between py-3">
          <Logo />
          <div className="flex items-center gap-2">
            <Link href="/login" className="text-brown-700 font-medium px-3 py-2 text-sm">Connexion</Link>
            <Link href="/signup" className="btn-primary !py-2 text-sm">S'inscrire</Link>
          </div>
        </div>
      </header>
      <main className="container py-6">{children}</main>
    </>
  );
}

export function UpsellBanner({ upsell, text }: { upsell: { id: number; name: string; price: string } | null; text?: string }) {
  return (
    <div className="card border-caramel bg-brown-50 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p className="font-semibold">{text ?? 'Débloquez le cours complet, tous les quiz et les examens blancs'}</p>
        {upsell && <p className="text-sm text-brown-800/70">{upsell.name} — à partir de {Number(upsell.price).toLocaleString('fr-FR')} €</p>}
      </div>
      <Link href={upsell ? `/signup?offer=${upsell.id}` : '/#tarifs'} className="btn-primary">{upsell ? 'Choisir cette offre' : 'Voir les offres'}</Link>
    </div>
  );
}
