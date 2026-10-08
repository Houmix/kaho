import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { ActivityEntry, Paginated } from '@/lib/admin';

export const KIND_STYLE: Record<string, string> = {
  BOOKING: 'bg-brown-700 text-cream-50', CANCELLATION: 'bg-cream-200 text-brown-800', LATE_CANCELLATION: 'bg-caramel/50 text-brown-900',
  NO_SHOW: 'bg-red-100 text-red-700', REFUND: 'bg-cream-200 text-brown-800', SLOT_MOVED: 'bg-caramel/30 text-brown-900',
  PAYMENT: 'bg-brown-500 text-cream-50', HOURS_ADDED: 'bg-brown-300 text-brown-900', APPLICATION: 'bg-cream-200 text-brown-800',
  INSTRUCTOR: 'bg-cream-200 text-brown-800', LESSON: 'bg-cream-200 text-brown-800', REMINDERS: 'bg-cream-100 text-brown-800/70',
};
const KINDS = [
  ['', 'Tout'], ['BOOKING,CANCELLATION,LATE_CANCELLATION,SLOT_MOVED', 'Réservations'], ['NO_SHOW,REFUND', 'Absences & re-crédits'],
  ['PAYMENT,HOURS_ADDED', 'Paiements'], ['APPLICATION,INSTRUCTOR', 'Moniteurs'], ['REMINDERS', 'Rappels'],
];

export function ActivityList({ items }: { items: ActivityEntry[] }) {
  return (
    <ul className="divide-y divide-cream-200">
      {items.map((e) => (
        <li key={e.id} className="py-2 flex gap-3 text-sm">
          <span className="text-brown-800/50 whitespace-nowrap w-28 shrink-0">{new Date(e.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
          <span className={`badge shrink-0 ${KIND_STYLE[e.kind] || 'bg-cream-200 text-brown-800'}`}>{e.kind_display}</span>
          <span className="flex-1">
            {e.message}
            {e.actor_name && <span className="text-brown-800/50"> — par {e.actor_name}</span>}
            {e.student && <> · <Link href={`/admin/students/${e.student}`} className="text-brown-700 hover:underline">élève</Link></>}
            {e.instructor && <> · <Link href={`/admin/instructors/${e.instructor}`} className="text-brown-700 hover:underline">moniteur</Link></>}
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function AdminActivity() {
  const ready = useRequireAuth(['SUPERVISOR', 'ADMIN']);
  const [kind, setKind] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<ActivityEntry> | null>(null);
  const load = useCallback(() => api.get('/admin/activity/', { params: { kind: kind || undefined, page, page_size: 50 } }).then((r) => setData(r.data)), [kind, page]);
  useEffect(() => { if (ready) load(); }, [ready, load]);
  const pages = data ? Math.max(1, Math.ceil(data.count / 50)) : 1;

  return (
    <AdminShell title="Activité">
      <h1 className="text-3xl mb-2">Historique d'activité</h1>
      <p className="text-brown-800/70 mb-6">Réservations, annulations, absences, re-crédits, paiements, candidatures, rappels envoyés.</p>
      <div className="flex flex-wrap gap-1 mb-4">{KINDS.map(([k, l]) => <button key={k} onClick={() => { setKind(k); setPage(1); }} className={`badge !px-3 !py-1.5 ${kind === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>)}</div>
      <div className="card">
        {!data ? <p className="text-brown-500">Chargement…</p> : data.results.length === 0 ? <p className="text-brown-800/60">Aucun événement.</p> : <ActivityList items={data.results} />}
      </div>
      {pages > 1 && <div className="flex items-center justify-end gap-2 mt-3 text-sm"><button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-secondary !py-1.5 disabled:opacity-40">←</button><span>Page {page} / {pages}</span><button disabled={page >= pages} onClick={() => setPage(page + 1)} className="btn-secondary !py-1.5 disabled:opacity-40">→</button></div>}
    </AdminShell>
  );
}
