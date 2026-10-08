import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { Overview } from '@/lib/admin';
import { formatPrice } from '@/lib/offers';
import { ActivityList } from './activity';

function Kpi({ label, value, sub, href, tone }: { label: string; value: string; sub?: string; href?: string; tone?: 'warn' }) {
  const inner = (
    <div className={`card py-4 h-full ${tone === 'warn' ? 'border-caramel bg-brown-50' : ''} ${href ? 'hover:border-brown-300 transition-colors' : ''}`}>
      <p className="text-sm text-brown-800/70">{label}</p>
      <p className="text-3xl font-display mt-1">{value}</p>
      {sub && <p className="text-xs text-brown-800/60 mt-1">{sub}</p>}
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}

const QUICK: { href: string; label: string; hint: string; owner?: boolean }[] = [
  { href: '/admin/students?new=1', label: 'Créer un élève', hint: 'Compte + offre + heures' },
  { href: '/admin/instructors?new=1', label: 'Ajouter un moniteur', hint: 'Invitation par email' },
  { href: '/admin/instructors?tab=applications', label: 'Valider un justificatif', hint: 'Candidatures moniteurs' },
  { href: '/admin/sales?tab=invoices', label: 'Factures & paie', hint: 'PDF, impayés, heures moniteurs', owner: true },
  { href: '/admin/instructors?tab=absences', label: 'Valider une absence', hint: 'Congés et arrêts des moniteurs' },
  { href: '/admin/team', label: 'Gérer l’équipe admin', hint: 'Comptes et permissions', owner: true },
];

export default function AdminHome() {
  const ready = useRequireAuth(BACKOFFICE);
  const { user } = useAuth();
  const isOwner = user?.role === 'OWNER';
  const [d, setD] = useState<Overview | null>(null);

  useEffect(() => { if (ready) api.get('/admin/overview/').then((r) => setD(r.data)); }, [ready]);

  if (!d) return <AdminShell title="Tableau de bord"><p className="text-brown-500">Chargement…</p></AdminShell>;

  return (
    <AdminShell title="Tableau de bord">
      <h1 className="text-3xl mb-6">Tableau de bord</h1>

      {d.alerts.length > 0 && (
        <section className="mb-6 space-y-2">
          {d.alerts.map((a) => (
            <Link key={a.kind} href={a.href} className="card py-3 flex items-center justify-between gap-3 border-caramel bg-brown-50 hover:border-brown-500">
              <span><span className="badge bg-caramel text-brown-900 mr-2">{a.count}</span>{a.text}</span>
              <span className="text-brown-700 text-sm">Traiter →</span>
            </Link>
          ))}
        </section>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {isOwner && <Kpi label={`Chiffre d'affaires — ${d.month.label}`} value={formatPrice(d.month.revenue)} sub={`${d.month.sales} vente${d.month.sales > 1 ? 's' : ''} encaissée${d.month.sales > 1 ? 's' : ''}`} href="/admin/sales" />}
        <Kpi label="Élèves actifs" value={String(d.students.active)} sub={`sur ${d.students.total} inscrits`} href="/admin/students" />
        <Kpi label="Taux d'occupation (semaine)" value={d.occupancy.percent === null ? '—' : `${d.occupancy.percent} %`} sub={`${d.occupancy.booked_hours} h réservées / ${d.occupancy.opened_hours} h ouvertes`} href="/admin/calendar" />
        <Kpi label="Note moyenne des moniteurs" value={d.rating.average === null ? '—' : `${d.rating.average.toFixed(1)} / 5`} sub={`${d.rating.count} avis`} href="/admin/reviews" />
        <Kpi label="Paiements en attente" value={isOwner ? formatPrice(d.unpaid.amount) : String(d.unpaid.count)} sub={`${d.unpaid.count} achat${d.unpaid.count > 1 ? 's' : ''} en attente`} href={isOwner ? '/admin/sales' : '/admin/students?filter=unpaid'} tone={d.unpaid.count ? 'warn' : undefined} />
        <Kpi label="Leçons aujourd'hui" value={String(d.today.lessons)} sub={`${d.today.to_review} bilan${d.today.to_review > 1 ? 's' : ''} à saisir`} href="/admin/calendar" />
        <Kpi label="Moniteurs réservables" value={`${d.instructors.bookable} / ${d.instructors.total}`} sub={d.instructors.without_password ? `${d.instructors.without_password} n'ont pas encore activé leur compte` : 'Tous les comptes sont actifs'} href="/admin/instructors" />
        <Kpi label="Absences / annul. tardives (semaine)" value={String(d.today.no_shows_week)} href="/instructor/planning" />
      </div>

      <h2 className="text-xl mb-3">Actions rapides</h2>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {QUICK.filter((q) => !q.owner || isOwner).map((q) => (
          <Link key={q.href} href={q.href} className="card py-4 hover:border-brown-300 transition-colors">
            <div className="font-semibold">{q.label} →</div>
            <div className="text-sm text-brown-800/60">{q.hint}</div>
          </Link>
        ))}
      </div>

      <div className="flex items-center justify-between mb-3"><h2 className="text-xl">Dernière activité</h2><Link href="/admin/activity" className="text-sm text-brown-700 hover:underline">Tout l'historique →</Link></div>
      <div className="card">{d.activity.length === 0 ? <p className="text-sm text-brown-800/60">Aucun événement pour le moment.</p> : <ActivityList items={d.activity} />}</div>
    </AdminShell>
  );
}
